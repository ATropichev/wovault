#!/usr/bin/env python3
"""G0 lab control: allowlist verification, reset, cleanup, canary scan/redact.

All state-changing commands enforce lab/resources.json: only paths inside the
task-owned prefixes (lab-output/) and containers named wov-g000-* are operated
on; everything else is refused. The executable target allowlist is
lab/targets.json.

Commands:
    verify-allowlist [--targets PATH] [--json]
    resolve --target NAME
    reset --scope DIR --baseline DIR
    cleanup [--apply] [--path PATH ...] [--containers]
    scan --paths PATH [PATH ...] [--allow PATH ...]
    redact --in FILE --out FILE

Exit codes: 0 success/clean, 2 verification failure or incomplete scan
coverage, 3 refused (resource outside the task-owned allowlist or a target
that is not activated), 1 canary hits found or usage/IO error.
"""
import argparse
import fnmatch
import ipaddress
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB = REPO_ROOT / "lab"
TARGETS_PATH = LAB / "targets.json"
RESOURCES_PATH = LAB / "resources.json"
PINS_PATH = LAB / "fixtures" / "pins.json"

LOOPBACK = (ipaddress.ip_network("127.0.0.0/8"), ipaddress.ip_network("::1/128"))
DOC_NETS = (ipaddress.ip_network("192.0.2.0/24"),
            ipaddress.ip_network("198.51.100.0/24"),
            ipaddress.ip_network("203.0.113.0/24"))
CONTAINER_PREFIX = "wov-g000-"


class Refused(Exception):
    pass


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def owned_prefixes():
    """Task-owned prefixes exactly as configured in resources.json."""
    doc = load_json(RESOURCES_PATH)
    return [p.rstrip("/") for p in doc["filesystem"]["owned_path_prefixes"]]


def owned_roots():
    """Task-owned prefixes as lexical absolute paths, never resolved through
    symlinks: a symlinked lab-output (or a symlink inside it) must not make
    its target directory count as task-owned."""
    return [Path(os.path.normpath(REPO_ROOT / p)) for p in owned_prefixes()]


def resolve_owned(path):
    """Resolve PATH to a real path inside a task-owned prefix, or raise Refused.

    The requested path is fully resolved so '..' and symlinks inside it are
    exposed; the owned roots are compared lexically from the (already
    resolved) repository root. Anything that resolves outside them — including
    through a symlinked owned prefix — is refused."""
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    p = p.resolve()
    for root in owned_roots():
        if p == root or root in p.parents:
            return p
    raise Refused(f"{path} resolves outside task-owned prefixes "
                  f"{owned_prefixes()}")


def resolve_target(name, targets_doc=None):
    doc = targets_doc or load_json(TARGETS_PATH)
    for t in doc.get("targets", []):
        if t["name"] == name and t.get("authorized") and t.get("disposable"):
            return t
    raise Refused(f"target '{name}' is not in the executable allowlist")


# ---------------------------------------------------------------- allowlist

def check_address(entry, where, errors):
    """Executable targets may only have no address, a loopback address or a
    container-internal wov-g000-* name. Documentation-range IPs are allowed
    only as topology role identifiers (doc_address), never as a dial address."""
    addr = entry.get("address")
    cls = entry.get("address_class")
    if addr in (None, "", "none"):
        if cls not in ("none", None):
            errors.append(f"{where}: address is empty but address_class={cls!r}")
        return
    try:
        ip = ipaddress.ip_address(addr)
        if not any(ip in net for net in LOOPBACK):
            errors.append(f"{where}: address {addr} is not loopback; only "
                          "loopback/none/container-internal targets are executable")
        return
    except ValueError:
        pass
    if isinstance(addr, str) and addr.startswith(CONTAINER_PREFIX):
        return
    errors.append(f"{where}: address {addr!r} is not loopback, none or "
                  f"{CONTAINER_PREFIX}*")


def verify_allowlist(doc):
    errors = []
    budget = doc.get("resource_budget")
    if not isinstance(budget, dict) or not budget:
        errors.append("resource_budget: missing or empty")
    else:
        for k, v in budget.items():
            if isinstance(v, (int, float)) and v <= 0:
                errors.append(f"resource_budget.{k}: must be positive")
    for i, role in enumerate(doc.get("topology_roles", [])):
        w = f"topology_roles[{i}]"
        addr = role.get("doc_address")
        try:
            ip = ipaddress.ip_address(addr)
            if not any(ip in n for n in DOC_NETS):
                errors.append(f"{w}: doc_address {addr} is not a documentation-range IP")
        except ValueError:
            errors.append(f"{w}: doc_address {addr!r} must be a documentation-range IP")
    targets = doc.get("targets", [])
    if not targets:
        errors.append("targets: no executable targets defined")
    for i, t in enumerate(targets):
        w = f"targets[{i}] ({t.get('name', '?')})"
        for field in ("name", "kind", "owner", "reset", "cleanup", "limits"):
            if not t.get(field):
                errors.append(f"{w}: missing '{field}'")
        if t.get("authorized") is not True:
            errors.append(f"{w}: authorized must be true")
        if t.get("disposable") is not True:
            errors.append(f"{w}: disposable must be true; only disposable targets are allowed")
        check_address(t, w, errors)
    for i, t in enumerate(doc.get("pending_targets", [])):
        w = f"pending_targets[{i}] ({t.get('name', '?')})"
        if t.get("authorized") is not False:
            errors.append(f"{w}: pending targets must keep authorized=false "
                          "until coordinator activation")
    return errors


def cmd_verify(args):
    doc = load_json(args.targets)
    errors = verify_allowlist(doc)
    result = {
        "targets": [t["name"] for t in doc.get("targets", [])],
        "pending": [t["name"] for t in doc.get("pending_targets", [])],
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for name in result["targets"]:
            print(f"executable: {name}")
        for name in result["pending"]:
            print(f"pending (not executable): {name}")
        for e in errors:
            print(f"ERROR {e}")
        print("allowlist: " + ("OK" if not errors else "FAILED"))
    return 0 if not errors else 2


def cmd_resolve(args):
    try:
        t = resolve_target(args.target)
    except Refused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return 3
    print(json.dumps(t, indent=2))
    return 0


# ---------------------------------------------------------------- reset

def dir_manifest(root):
    import hashlib
    entries = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            entries.append((str(p.relative_to(root)),
                            hashlib.sha256(p.read_bytes()).hexdigest()))
    return entries


def cmd_reset(args):
    try:
        scope = resolve_owned(args.scope)
        baseline = resolve_owned(args.baseline)
    except Refused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return 3
    if scope == baseline or scope in baseline.parents or baseline in scope.parents:
        print("REFUSED scope and baseline overlap; reset would destroy the "
              "baseline it restores from", file=sys.stderr)
        return 3
    if not baseline.is_dir():
        print(f"baseline {baseline} does not exist or is not a directory", file=sys.stderr)
        return 1
    before = dir_manifest(scope) if scope.exists() else []
    if scope.exists():
        shutil.rmtree(scope)
    shutil.copytree(baseline, scope)
    after = dir_manifest(scope)
    restored = sorted(p for p, _ in set(dir_manifest(baseline)) - set(before))
    removed = sorted(p for p, _ in set(before) - set(after))
    print(json.dumps({
        "reset": "ok", "scope": str(scope.relative_to(REPO_ROOT)),
        "restored_or_rewritten": restored, "removed_strays": removed,
        "matches_baseline": after == dir_manifest(baseline),
    }, indent=2))
    return 0 if after == dir_manifest(baseline) else 2


# ---------------------------------------------------------------- cleanup

def cmd_cleanup(args):
    if args.containers:
        # Coordinator-run profile only; enforce the name prefix regardless.
        return cleanup_containers(args)
    paths = args.path or ["lab-output/"]
    removed, refused, leftovers = [], [], []
    for raw in paths:
        try:
            p = resolve_owned(raw)
        except Refused as exc:
            refused.append(str(raw))
            print(f"REFUSED {exc}", file=sys.stderr)
            continue
        if not p.exists():
            leftovers.append(f"{raw} (already absent)")
            continue
        if args.apply:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            removed.append(str(raw))
        else:
            leftovers.append(f"{raw} (would remove)")
    if args.apply:
        for raw in list(removed):
            p = (REPO_ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
            if p.exists():
                leftovers.append(f"{raw} (still present)")
    result = {"performed": bool(args.apply), "verified": args.apply
              and not refused and not any(
        "still present" in x for x in leftovers),
        "resources_removed": removed, "refused": refused, "leftovers": leftovers}
    print(json.dumps(result, indent=2))
    return 3 if refused else 0


def activated_container_target():
    """The single activated container-set target from the executable allowlist.

    An entry in pending_targets is definitionally not activated: the coordinator
    must move it into 'targets' with authorized=true first. Refuses without
    contacting any container daemon."""
    doc = load_json(TARGETS_PATH)
    for t in doc.get("targets", []):
        if t.get("kind") == "container-set":
            if t.get("authorized") is True and t.get("disposable") is True:
                return t
    pending = [t.get("name", "?") for t in doc.get("pending_targets", [])
               if t.get("kind") == "container-set"]
    raise Refused("no activated container-set target in the executable "
                  "allowlist" + (f"; pending targets {pending} require "
                  "coordinator activation first" if pending else ""))


def docker_endpoint_local():
    """Whether the configured Docker endpoint is an approved local daemon.

    Only an unset DOCKER_HOST or a local unix/npipe/fd endpoint is approved,
    and only the default context. A remote host or a named non-default context
    is refused before any daemon contact so a pending profile can never dial
    an arbitrary Docker context."""
    ctx = os.environ.get("DOCKER_CONTEXT", "")
    if ctx and ctx != "default":
        return False, f"DOCKER_CONTEXT={ctx!r} is not the approved default local context"
    host = os.environ.get("DOCKER_HOST", "")
    if host:
        scheme = host.split("://", 1)[0] if "://" in host else (
            "unix" if host.startswith("/") else host.split(":", 1)[0])
        if scheme not in ("unix", "npipe", "fd"):
            return False, f"DOCKER_HOST={host!r} is not a local daemon endpoint"
    return True, ""


def cleanup_containers(args):
    """Remove only wov-g000-* containers, and only for the activated
    container-set target against the approved local daemon. Refuses without
    contacting Docker while the target is pending or the endpoint is remote;
    fails closed when the local daemon is unreachable rather than touching
    anything."""
    import subprocess
    try:
        activated_container_target()
    except Refused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return 3
    ok, why = docker_endpoint_local()
    if not ok:
        print(f"REFUSED {why}", file=sys.stderr)
        return 3
    proc = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True, timeout=15)
    if proc.returncode != 0:
        print(json.dumps({"performed": False, "verified": False,
                          "blocker": f"docker daemon unreachable: {proc.stderr.strip()}",
                          "resources_removed": [], "refused": [], "leftovers": []}, indent=2))
        return 2
    removed, refused, leftovers = [], [], []
    for name in proc.stdout.split():
        if name.startswith(CONTAINER_PREFIX):
            if args.apply:
                rm = subprocess.run(["docker", "rm", "-f", name], check=False,
                                    capture_output=True, text=True)
                if rm.returncode == 0:
                    removed.append(name)
                else:
                    leftovers.append(f"{name} (removal failed: "
                                     f"{(rm.stderr or rm.stdout).strip() or 'exit ' + str(rm.returncode)})")
            else:
                leftovers.append(f"{name} (would remove)")
        else:
            refused.append(name)
    verified = bool(args.apply) and not leftovers
    print(json.dumps({"performed": bool(args.apply), "verified": verified,
                      "resources_removed": removed, "refused": refused,
                      "leftovers": leftovers}, indent=2))
    return 2 if args.apply and leftovers else 0


# ---------------------------------------------------------------- canaries

def canary_values():
    pins = load_json(PINS_PATH)
    return {c["id"]: c["value"] for c in pins["canaries"]}


def iter_files(paths, errors):
    """Yield scannable files under PATHS; anything that cannot be scanned is an
    error, not a silent skip — a scan that missed input is not a clean scan."""
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            yield from sorted(x for x in p.rglob("*") if x.is_file())
        elif p.is_file():
            yield p
        elif p.exists():
            errors.append(f"not a scannable file or directory: {raw}")
        else:
            errors.append(f"missing input path: {raw}")


def cmd_scan(args):
    """Byte-scan PATHS for the pinned canary values.

    Scanning happens on raw bytes so binary and non-UTF-8 files are covered.
    A missing path or unreadable file makes coverage incomplete and returns
    exit 2 (non-success) even when no canary is found; hits return 1."""
    import re
    needles = {cid: v.encode("utf-8") for cid, v in canary_values().items()}
    allow_re = [re.compile(fnmatch.translate(a)) for a in (args.allow or [])]
    hits, errors, scanned = [], [], 0
    for path in iter_files(args.paths, errors):
        rp = path.resolve()
        rel = str(rp.relative_to(REPO_ROOT)) if rp.is_relative_to(REPO_ROOT) else str(rp)
        if any(r.match(rel) for r in allow_re):
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            errors.append(f"unreadable file: {rel} ({exc.strerror or exc})")
            continue
        scanned += 1
        for cid, needle in needles.items():
            start = 0
            while True:
                i = data.find(needle, start)
                if i < 0:
                    break
                hits.append({"path": rel,
                             "line": data.count(b"\n", 0, i) + 1,
                             "canary_id": cid})
                start = i + 1
    print(json.dumps({"scanned_files": scanned, "hits": hits, "errors": errors,
                      "coverage": "complete" if not errors else "incomplete"},
                     indent=2))
    if errors:
        return 2
    return 1 if hits else 0


def cmd_redact(args):
    """Replace pinned canary values with REDACTED:<id>, byte-exact."""
    src = Path(args.in_path)
    data = src.read_bytes()
    counts = {}
    for cid, value in canary_values().items():
        needle = value.encode("utf-8")
        n = data.count(needle)
        if n:
            data = data.replace(needle, f"REDACTED:{cid}".encode("utf-8"))
            counts[cid] = n
    try:
        out = resolve_owned(args.out)
    except Refused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return 3
    out.write_bytes(data)
    print(json.dumps({"redacted": counts, "out": str(args.out)}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("verify-allowlist")
    p.add_argument("--targets", type=Path, default=TARGETS_PATH)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("resolve")
    p.add_argument("--target", required=True)
    p.set_defaults(fn=cmd_resolve)

    p = sub.add_parser("reset")
    p.add_argument("--scope", required=True)
    p.add_argument("--baseline", required=True)
    p.set_defaults(fn=cmd_reset)

    p = sub.add_parser("cleanup")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--path", action="append")
    p.add_argument("--containers", action="store_true")
    p.set_defaults(fn=cmd_cleanup)

    p = sub.add_parser("scan")
    p.add_argument("--paths", nargs="+", required=True)
    p.add_argument("--allow", action="append")
    p.set_defaults(fn=cmd_scan)

    p = sub.add_parser("redact")
    p.add_argument("--in", dest="in_path", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_redact)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
