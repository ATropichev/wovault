#!/usr/bin/env python3
"""Run the G0-00 lab checks and emit schema-valid evidence reports.

Groups (matching validate-g0-feasibility/tasks.md group 1):
    targets    task 1.1 — allowlist contents, refusal of non-allowlisted
               resources, pending targets not executable
    fixtures   task 1.2 — deterministic generation, pinned manifests,
               synthetic-content scan
    schema     task 1.3 — validator accepts valid reports, rejects missing
               fields and fabricated passes
    isolation  task 1.4 — bwrap namespace egress/filesystem isolation,
               baseline reset, canary redaction/detection (AC-26/AC-33)

Each group runs inside its own task-owned workdir (<workdir>/<group>), emits
a g0-evidence/1 report plus artifacts into --publish (which must stay inside
lab/evidence/runs/), and is finalized with a cleanup record on success,
failure or harness exception; --no-cleanup is recorded explicitly. Only
values that ran get a tested-* verdict; unavailable prerequisites yield
blocked, never a fabricated pass. The command exits non-zero when any report
is invalid, any scenario is tested-fail, or a group crashes — a valid report
is not the same as a successful experiment.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB = REPO_ROOT / "lab"
LAB_OUT = REPO_ROOT / "lab-output"
LABCTL = LAB / "tools" / "labctl.py"
GENERATE = LAB / "fixtures" / "generate.py"
VALIDATE = LAB / "evidence" / "validate.py"
PINS_PATH = LAB / "fixtures" / "pins.json"
PAYLOAD = LAB / "tools" / "payloads" / "restore_sim.py"
PUBLISH_DIR = LAB / "evidence" / "runs"

sys.dont_write_bytecode = True
sys.path.insert(0, str(LAB / "evidence"))
import validate as evidence_validate  # noqa: E402
sys.path.insert(0, str(LAB / "tools"))
import labctl  # noqa: E402

TASK = "CR-001"
CHANGE = "validate-g0-feasibility"
ACTOR = os.environ.get("AGENTMARSHAL_ACTOR", "agent-devin")


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sh(cmd, timeout=120, cwd=REPO_ROOT, env=None):
    """Run a command and capture a real run record."""
    ran_at = utcnow()
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, cwd=cwd, env=env)
        return {"cmd": cmd, "exit_code": proc.returncode,
                "stdout": proc.stdout, "stderr": proc.stderr,
                "ran_at": ran_at,
                "duration_ms": round((time.monotonic() - start) * 1000, 1)}
    except FileNotFoundError as exc:
        return {"cmd": cmd, "exit_code": None, "stdout": "",
                "stderr": str(exc), "ran_at": ran_at,
                "duration_ms": round((time.monotonic() - start) * 1000, 1),
                "missing": True}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def rel(path):
    return str(Path(path).resolve().relative_to(REPO_ROOT))


def sanitize(data):
    """Strip workstation-private absolute prefixes from retained evidence
    bytes: the repository root and the user's home become <repo>/<home>
    placeholders. Digests are computed after sanitization so they always
    match the published content."""
    for raw, marker in ((REPO_ROOT, b"<repo>"), (Path.home(), b"<home>")):
        data = data.replace(str(raw).encode(), marker)
    return data


def sanitize_report(value):
    """Sanitize every report string before JSON escaping and publication."""
    if isinstance(value, str):
        return sanitize(value.encode("utf-8")).decode("utf-8")
    if isinstance(value, list):
        return [sanitize_report(item) for item in value]
    if isinstance(value, dict):
        return {sanitize_report(key): sanitize_report(item)
                for key, item in value.items()}
    return value


class Artifacts:
    """Retained evidence files for one report, written directly into the
    publish directory so report paths match committed locations."""

    def __init__(self, dest_dir):
        self.dest_dir = resolve_publish(dest_dir)
        self.dest_dir.mkdir(parents=True, exist_ok=True)
        self.entries = []

    def save(self, name, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        data = sanitize(data)
        path = resolve_publish(self.dest_dir / name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        entry = {"name": name, "sha256": sha256_bytes(data),
                 "path": str(path.relative_to(REPO_ROOT))}
        self.entries.append(entry)
        return entry

    def evidence(self, entry, note=None):
        ev = {"kind": "file", "path": entry["path"], "sha256": entry["sha256"]}
        if note:
            ev["note"] = note
        return ev


class Scenario:
    def __init__(self, sid, expected, title=None, fault_point=None):
        self.d = {"id": sid, "expected": expected}
        if title:
            self.d["title"] = title
        if fault_point:
            self.d["fault_point"] = fault_point

    def tested(self, passed, run, summary, evidence):
        self.d["verdict"] = "tested-pass" if passed else "tested-fail"
        self.d["actual"] = {"summary": summary, "exit_code": run["exit_code"]
                            if run["exit_code"] is not None else 127,
                            "ran_at": run["ran_at"],
                            "duration_ms": run["duration_ms"]}
        self.d["evidence"] = evidence
        return passed

    def blocked(self, blocker):
        self.d["verdict"] = "blocked"
        self.d["blocker"] = blocker
        return False

    def unknown(self):
        self.d["verdict"] = "unknown"
        return False

    def planned(self):
        self.d["verdict"] = "planned"
        return False

    def documented(self, source):
        self.d["verdict"] = "documented"
        self.d["source"] = source
        return False


def environment():
    env = {"os": platform.system().lower() or "linux",
           "arch": platform.machine() or "unknown",
           "kernel": platform.release(),
           "python": platform.python_version()}
    tools = {}
    for name, cmd in (("bwrap", ["bwrap", "--version"]),
                      ("unshare", ["unshare", "--version"]),
                      ("docker", ["docker", "--version"])):
        r = sh(cmd, timeout=10)
        if r["exit_code"] == 0:
            tools[name] = (r["stdout"] or r["stderr"]).strip().splitlines()[0]
    if tools:
        env["tools"] = tools
    return env


def base_report(report_id, req_ids, ac_ids):
    return {
        "schema_version": "g0-evidence/1",
        "report_id": report_id,
        "task": TASK,
        "change": CHANGE,
        "generated_at": utcnow(),
        "executor": {"actor": ACTOR, "profile": "local-namespace",
                     "environment": environment()},
        "target": {"name": "local-sandbox", "kind": "local-namespace",
                   "authorized": True,
                   "roles": ["control", "fixture-workspace", "isolation-check",
                             "reset-check", "canary-check"]},
        "requirement_ids": req_ids,
        "ac_ids": ac_ids,
        "scenarios": [],
        # G0-00 is protocol scaffolding, not a backup: every assurance
        # dimension stays explicitly not_checked. A dimension may only leave
        # not_checked when a tested-* scenario declares it via 'dimensions'.
        "assurance": {k: "not_checked" for k in
                      ("transfer", "completeness", "consistency",
                       "integrity", "restore_test", "security")},
    }


def finalize(report, artifacts, publish_dir, cleanup_block=None):
    if cleanup_block:
        report["cleanup"] = cleanup_block
    report["artifacts"] = [
        {"path": e["path"], "sha256": e["sha256"]} for e in artifacts.entries]
    dest = resolve_publish(publish_dir)
    dest.mkdir(parents=True, exist_ok=True)
    rpath = resolve_publish(dest / f"{report['report_id']}.json")
    rpath.write_text(json.dumps(sanitize_report(report), indent=2, sort_keys=False) + "\n",
                     encoding="utf-8")
    rep = evidence_validate.validate(json.loads(rpath.read_text()),
                                     evidence_validate.load_json(LAB / "targets.json"))
    if rep.errors:
        print(f"INTERNAL ERROR: generated report {rpath} failed validation:",
              file=sys.stderr)
        for e in rep.errors:
            print(f"  - {e}", file=sys.stderr)
        return rpath, False
    return rpath, True


def ev_stdout(run, artifacts, name, note=None):
    entry = artifacts.save(name, run["stdout"] or run["stderr"])
    return artifacts.evidence(entry, note)


# ------------------------------------------------------------------ targets

def check_targets(workdir, publish):
    report = base_report("g0-00-targets", ["NFR-02"], ["AC-33"])
    sc = report["scenarios"]
    art = Artifacts(Path(publish) / report["report_id"])

    s = Scenario("allowlist-verify",
                 "every executable target is disposable, authorized and has no "
                 "production address; pending targets stay non-executable")
    run = sh(["python3", str(LABCTL), "verify-allowlist", "--json"])
    doc = json.loads(run["stdout"]) if run["stdout"] else {}
    ok = run["exit_code"] == 0 and doc.get("errors") == [] and \
        doc.get("targets") == ["local-sandbox"] and \
        "wov-g000-containers" in doc.get("pending", [])
    s.tested(ok, run, f"exit={run['exit_code']}; executable={doc.get('targets')}; "
             f"pending={doc.get('pending')}; errors={doc.get('errors')}",
             [ev_stdout(run, art, "verify-allowlist.json")])
    sc.append(s.d)

    s = Scenario("allowlist-rejects-production",
                 "a doctored allowlist adding an executable target with a "
                 "non-allowlisted (non-loopback) address is rejected")
    doctored = json.loads((LAB / "targets.json").read_text())
    doctored["targets"].append({
        "name": "sneaky-prod", "kind": "remote-vps", "authorized": True,
        "disposable": True, "owner": "CR-001", "address_class": "production",
        "address": "192.0.2.99", "roles": ["source"],
        "reset": "x", "cleanup": "x", "limits": {"disk_mib": 1}})
    bad = art.save("doctored-targets.json",
                   json.dumps(doctored, indent=2))
    run = sh(["python3", str(LABCTL), "verify-allowlist",
              "--targets", bad["path"]])
    ok = run["exit_code"] == 2 and "192.0.2.99" in run["stdout"]
    s.tested(ok, run, f"doctored allowlist exit={run['exit_code']}; "
             "verifier must list the forbidden address",
             [ev_stdout(run, art, "verify-doctored.txt"),
              art.evidence(bad, "doctored input")])
    sc.append(s.d)

    s = Scenario("pending-target-not-executable",
                 "labctl resolve refuses the coordinator-owned pending "
                 "container target")
    run = sh(["python3", str(LABCTL), "resolve", "--target", "wov-g000-containers"])
    s.tested(run["exit_code"] == 3, run,
             f"resolve exit={run['exit_code']} (3=refused): {run['stderr'].strip()}",
             [ev_stdout(run, art, "resolve-pending.txt")])
    sc.append(s.d)

    s = Scenario("cleanup-refuses-unowned",
                 "cleanup --apply refuses a tracked, non-owned path and "
                 "leaves it untouched")
    sentinel = LAB / "topology.md"
    digest_before = sha256_file(sentinel)
    run = sh(["python3", str(LABCTL), "cleanup", "--apply", "--path", "lab/topology.md"])
    ok = run["exit_code"] == 3 and sentinel.exists() and \
        sha256_file(sentinel) == digest_before
    s.tested(ok, run, f"cleanup exit={run['exit_code']}; file intact="
             f"{sentinel.exists() and sha256_file(sentinel) == digest_before}",
             [ev_stdout(run, art, "cleanup-refuse.txt")])
    sc.append(s.d)

    s = Scenario("cleanup-refuses-symlink-escape",
                 "a symlink inside the owned prefix pointing outside the "
                 "workspace is refused and its target left untouched")
    esc_dir = Path(workdir) / "symlink-check"
    esc_dir.mkdir(parents=True, exist_ok=True)
    link = esc_dir / "escape"
    link.symlink_to(REPO_ROOT / "docs")
    run = sh(["python3", str(LABCTL), "cleanup", "--apply", "--path",
              str(link.relative_to(REPO_ROOT))])
    ok = run["exit_code"] == 3 and (REPO_ROOT / "docs").is_dir() and \
        link.is_symlink()
    s.tested(ok, run, f"cleanup exit={run['exit_code']} (3=refused); docs/ "
             f"intact={(REPO_ROOT / 'docs').is_dir()}: {run['stderr'].strip()}",
             [ev_stdout(run, art, "cleanup-symlink-refuse.txt")])
    sc.append(s.d)

    s = Scenario("containers-require-activation",
                 "cleanup --containers refuses while the container-set "
                 "target is pending, and refuses a non-local Docker endpoint "
                 "or context — without contacting any daemon",
                 fault_point="pending profile silently enumerates/removes "
                 "prefix-matching containers on an arbitrary Docker context")
    probes = {
        "plain-env": sh(["python3", str(LABCTL), "cleanup", "--containers"],
                        timeout=30),
        "remote-docker-host": sh(
            ["python3", str(LABCTL), "cleanup", "--containers"], timeout=30,
            env={**os.environ, "DOCKER_HOST": "tcp://203.0.113.7:2375"}),
        "dead-local-socket": sh(
            ["python3", str(LABCTL), "cleanup", "--containers"], timeout=30,
            env={**os.environ,
                 "DOCKER_HOST": "unix:///wov-g000-nonexistent.sock"}),
        "named-context": sh(
            ["python3", str(LABCTL), "cleanup", "--containers"], timeout=30,
            env={**os.environ, "DOCKER_CONTEXT": "wov-g000-remote-ctx"}),
    }
    ev = [ev_stdout(probes["plain-env"], art, "cleanup-containers-refuse.txt")]
    for name, r in list(probes.items())[1:]:
        ev.append(ev_stdout(r, art, f"cleanup-containers-{name}.txt"))
    ok = all(r["exit_code"] == 3 and "REFUSED" in r["stderr"]
             for r in probes.values())
    s.tested(ok, probes["plain-env"],
             "; ".join(f"{k}: exit={r['exit_code']} "
                       f"{r['stderr'].strip().splitlines()[0] if r['stderr'] else ''}"
                       for k, r in probes.items()), ev)
    sc.append(s.d)

    s = Scenario("generate-out-refuses-unowned",
                 "fixture generation refuses --out destinations outside the "
                 "task-owned prefix, including one that escapes through a "
                 "symlinked ancestor, and creates nothing there",
                 fault_point="arbitrary --out deletes a pre-existing "
                 "directory outside the lab workspace")
    probes = {}
    probes["tmp-out"] = sh(["python3", str(GENERATE), "generate",
                            "--out", "/tmp/wov-g0-evil-out"], timeout=30)
    link = Path(workdir) / "out-escape"
    link.symlink_to(REPO_ROOT / "docs")
    probes["symlink-out"] = sh(["python3", str(GENERATE), "generate",
                               "--out", str(link)], timeout=30)
    absent = not Path("/tmp/wov-g0-evil-out").exists()
    ok = all(r["exit_code"] == 3 for r in probes.values()) and absent \
        and not (link / "site-alpha").exists()
    ev = [ev_stdout(probes["tmp-out"], art, "generate-out-refuse.txt"),
          ev_stdout(probes["symlink-out"], art,
                    "generate-out-symlink-refuse.txt")]
    s.tested(ok, probes["tmp-out"],
             "; ".join(f"{k}: exit={r['exit_code']}" for k, r in probes.items())
             + f"; /tmp/wov-g0-evil-out absent={absent}", ev)
    sc.append(s.d)

    s = Scenario("workdir-refuses-unowned",
                 "run_checks refuses --workdir and --publish destinations "
                 "outside the task-owned prefix and the evidence directory "
                 "before creating anything",
                 fault_point="an arbitrary --workdir becomes a mutating "
                 "scratch root outside the allowlist")
    probe_wd = Path("/tmp/wov-g0-evil-workdir")
    probe_pub = Path("/tmp/wov-g0-evil-publish")
    r1 = sh(["python3", str(Path(__file__).resolve()), "targets",
             "--workdir", str(probe_wd)], timeout=30)
    r2 = sh(["python3", str(Path(__file__).resolve()), "targets",
             "--publish", str(probe_pub)], timeout=30)
    ok = r1["exit_code"] == 3 and r2["exit_code"] == 3 and \
        not probe_wd.exists() and not probe_pub.exists()
    s.tested(ok, r1, f"workdir exit={r1['exit_code']} (3=refused, "
             f"created={probe_wd.exists()}); publish exit={r2['exit_code']} "
             f"(created={probe_pub.exists()})",
             [ev_stdout(r1, art, "workdir-refuse.txt"),
              ev_stdout(r2, art, "publish-refuse.txt")])
    sc.append(s.d)

    return report, art


# ----------------------------------------------------------------- fixtures

def check_fixtures(workdir, publish):
    report = base_report("g0-00-fixtures", ["BKP-03", "NFR-05"], ["AC-33"])
    sc = report["scenarios"]
    art = Artifacts(Path(publish) / report["report_id"])
    fx = workdir / "fixture-trees"

    s = Scenario("generate-repeatable",
                 "two independent generation runs produce identical manifests "
                 "and digests")
    r1 = sh(["python3", str(GENERATE), "generate", "--out", str(fx / "run1")])
    r2 = sh(["python3", str(GENERATE), "generate", "--out", str(fx / "run2")])
    dig1 = sorted(sha256_file(p)
                  for p in (fx / "run1").glob("*.manifest.json"))
    dig2 = sorted(sha256_file(p) for p in (fx / "run2").glob("*.manifest.json"))
    manifests_equal = True
    for m1 in sorted((fx / "run1").glob("*.manifest.json")):
        m2 = fx / "run2" / m1.name
        if not m2.exists() or m1.read_bytes() != m2.read_bytes():
            manifests_equal = False
    ok = r1["exit_code"] == 0 and r2["exit_code"] == 0 and \
        manifests_equal and dig1 == dig2
    run = r1
    run["stdout"] = f"run1={dig1}\nrun2={dig2}\nbyte_equal={manifests_equal}\n"
    s.tested(ok, run, f"two generations byte-identical: {manifests_equal}; "
             f"digests equal: {dig1 == dig2}",
             [ev_stdout(run, art, "repeatability.txt")])
    sc.append(s.d)

    s = Scenario("matches-pinned-manifest",
                 "regeneration matches the committed expected manifests in "
                 "lab/fixtures/expected/")
    run = sh(["python3", str(GENERATE), "--check"])
    s.tested(run["exit_code"] == 0 and "MISMATCH" not in run["stdout"],
             run, run["stdout"].strip().replace("\n", "; "),
             [ev_stdout(run, art, "pinned-check.txt")])
    sc.append(s.d)

    s = Scenario("synthetic-content-only",
                 "fixture trees contain only documentation-range IPs, "
                 "example/invalid domains and the pinned canary tokens")
    import ipaddress as _ip
    import re as _re
    ip_re = _re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    dom_re = _re.compile(r"\b[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9-]+)+"
                         r"\.(?:com|net|org|io|test|invalid|dev|app|local)\b")
    doc_nets = [_ip.ip_network(n) for n in
                ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
    bad_ips, bad_domains = [], []
    scan_start = time.monotonic()
    scan_ran_at = utcnow()
    for f in sorted(fx.rglob("*")):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in ip_re.findall(text):
            try:
                ip = _ip.ip_address(m)
                if not any(ip in n for n in doc_nets):
                    bad_ips.append(f"{rel(f)}: {m}")
            except ValueError:
                bad_ips.append(f"{rel(f)}: {m}")
        for m in dom_re.findall(text):
            if not (m.endswith(".example.test") or m.endswith(".example.com")
                    or m.endswith(".invalid") or m in ("example.test", "example.com")):
                bad_domains.append(f"{rel(f)}: {m}")
    run = {"exit_code": 0 if not (bad_ips or bad_domains) else 1,
           "stdout": f"bad_ips={bad_ips}\nbad_domains={bad_domains}\n",
           "stderr": "", "ran_at": scan_ran_at,
           "duration_ms": round((time.monotonic() - scan_start) * 1000, 1)}
    s.tested(not (bad_ips or bad_domains), run,
             f"scanned {sum(1 for _ in fx.rglob('*') if _.is_file())} files; "
             f"non-doc IPs={bad_ips}; non-example domains={bad_domains}",
             [ev_stdout(run, art, "synthetic-scan.txt")])
    sc.append(s.d)

    s = Scenario("canary-placement",
                 "canary tokens appear exactly in the fixtures that pin them "
                 "and nowhere else")
    pins = json.loads(PINS_PATH.read_text())
    canaries = {c["id"]: c["value"] for c in pins["canaries"]}
    problems = []
    place_start = time.monotonic()
    place_ran_at = utcnow()
    for spec in pins["fixtures"]:
        tree = fx / "run1" / spec["name"]
        blob = ""
        for f in sorted(tree.rglob("*")):
            if f.is_file():
                try:
                    blob += f.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    pass
        for cid, value in canaries.items():
            present = value in blob
            expected = cid in spec.get("canary_ids", [])
            if present != expected:
                problems.append(f"{spec['name']}: canary {cid} "
                                f"{'missing' if expected else 'unexpected'}")
    run = {"exit_code": 0 if not problems else 1,
           "stdout": "\n".join(problems) or "all canaries correctly placed",
           "stderr": "", "ran_at": place_ran_at,
           "duration_ms": round((time.monotonic() - place_start) * 1000, 1)}
    s.tested(not problems, run, "; ".join(problems) if problems else
             "site-alpha carries 3 canaries; neighbors carry none",
             [ev_stdout(run, art, "canary-placement.txt")])
    sc.append(s.d)

    return report, art


# ------------------------------------------------------------------- schema

def check_schema(workdir, publish):
    report = base_report("g0-00-evidence-schema", ["VER-01", "NFR-02"],
                         ["AC-26", "AC-33"])
    sc = report["scenarios"]
    art = Artifacts(Path(publish) / report["report_id"])
    ex = LAB / "evidence" / "examples"
    # Invoke the validator with repo-relative paths only: absolute workstation
    # paths must never land in retained evidence artifacts.
    ex_rel = ex.relative_to(REPO_ROOT)

    s = Scenario("schema-document-loads",
                 "report.schema.json parses and declares the verdict enum and "
                 "conditional tested/non-tested rules")
    run = sh(["python3", "-c",
              "import json,sys; d=json.load(open(sys.argv[1])); "
              "print(sorted(d['$defs']['scenario']['properties']['verdict']['enum'])); "
              "print(len(d['$defs']['scenario']['allOf']))",
              str(LAB / "evidence" / "report.schema.json")])
    ok = run["exit_code"] == 0 and "tested-pass" in run["stdout"]
    s.tested(ok, run, run["stdout"].strip().replace("\n", "; "),
             [ev_stdout(run, art, "schema-load.txt")])
    sc.append(s.d)

    s = Scenario("selftest-passes",
                 "every valid-* example validates and every err-* example is "
                 "rejected")
    run = sh(["python3", str(VALIDATE), "--selftest"])
    ok = run["exit_code"] == 0 and "SELFTEST-FAIL" not in run["stdout"]
    s.tested(ok, run, run["stdout"].strip().replace("\n", "; "),
             [ev_stdout(run, art, "selftest.txt")])
    sc.append(s.d)

    s = Scenario("missing-fields-rejected",
                 "a report missing required fields is rejected with named "
                 "errors")
    run = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
              str(ex_rel / "err-missing-required.json")])
    ok = run["exit_code"] == 2 and "missing required field" in run["stdout"]
    s.tested(ok, run, f"exit={run['exit_code']}: "
             f"{run['stdout'].strip().splitlines()[-1] if run['stdout'] else ''}",
             [ev_stdout(run, art, "reject-missing.txt")])
    sc.append(s.d)

    s = Scenario("pass-without-run-rejected",
                 "tested-pass without an actual run record or evidence is "
                 "rejected")
    runs = {}
    for name in ("err-pass-without-actual.json", "err-pass-without-evidence.json"):
        runs[name] = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
                         str(ex_rel / name)])
    ok = all(r["exit_code"] == 2 for r in runs.values())
    s.tested(ok, runs["err-pass-without-actual.json"],
             "; ".join(f"{n}: exit={r['exit_code']}" for n, r in runs.items()),
             [ev_stdout(runs["err-pass-without-actual.json"], art,
                        "reject-fabricated-actual.txt"),
              ev_stdout(runs["err-pass-without-evidence.json"], art,
                        "reject-fabricated-evidence.txt")])
    sc.append(s.d)

    s = Scenario("unknown-is-not-a-pass",
                 "an unknown verdict validates but counts as zero tested-pass "
                 "scenarios, and unknown carrying run results is rejected")
    run = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)), "--summary",
              str(ex_rel / "valid-unknown-report.json")])
    doc = json.loads((ex / "valid-unknown-report.json").read_text())
    counts = evidence_validate.verdict_summary(doc)
    run2 = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
               str(ex_rel / "err-unknown-with-actual.json")])
    ok = run["exit_code"] == 0 and counts["tested-pass"] == 0 and \
        counts["unknown"] == 1 and run2["exit_code"] == 2
    s.tested(ok, run, f"valid report with unknown accepted; tested-pass "
             f"count={counts['tested-pass']}; unknown-with-actual rejected "
             f"exit={run2['exit_code']}",
             [ev_stdout(run, art, "unknown-summary.txt"),
              ev_stdout(run2, art, "reject-unknown-run.txt")])
    sc.append(s.d)

    s = Scenario("unauthorized-target-rejected",
                 "a report naming a non-allowlisted target is rejected")
    run = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
              str(ex_rel / "err-unauthorized-target.json")])
    s.tested(run["exit_code"] == 2, run,
             f"exit={run['exit_code']}: {run['stdout'].strip().splitlines()[-1]}",
             [ev_stdout(run, art, "reject-target.txt")])
    sc.append(s.d)

    s = Scenario("canonical-schema-agreement",
                 "the canonical validator never accepts a report the published "
                 "schema rejects; every schema-invalid example is also "
                 "canonical-invalid. The reverse is allowed where the canonical "
                 "validator adds checks the schema cannot express (the "
                 "targets.json allowlist cross-check)",
                 fault_point="canonical and published contract disagree "
                 "(F2 class)")
    try:
        import jsonschema
    except ImportError:
        s.blocked("jsonschema package not installed; schema/canonical "
                  "agreement could not be executed in this environment")
    else:
        agree_start = time.monotonic()
        agree_ran_at = utcnow()
        schema_doc = json.loads(
            (LAB / "evidence" / "report.schema.json").read_text())
        targets_doc = evidence_validate.load_json(LAB / "targets.json")
        bad, lines = [], []
        try:
            jsonschema.Draft202012Validator.check_schema(schema_doc)
            validator = jsonschema.Draft202012Validator(schema_doc)
            for path in sorted(ex.glob("*.json")):
                doc = json.loads(path.read_text())
                schema_ok = not list(validator.iter_errors(doc))
                canon_ok = not evidence_validate.validate(
                    doc, targets_doc).errors
                lines.append(f"{path.name}: schema={'valid' if schema_ok else 'invalid'} "
                             f"canonical={'valid' if canon_ok else 'invalid'}")
                if canon_ok and not schema_ok:
                    bad.append(path.name)
        except Exception as exc:  # schema itself failed to parse/compile
            bad.append(f"schema-error: {exc}")
        run = {"exit_code": 0 if not bad else 1,
               "stdout": "\n".join(lines) or "no examples found",
               "stderr": "", "ran_at": agree_ran_at,
               "duration_ms": round((time.monotonic() - agree_start) * 1000, 1)}
        s.tested(not bad, run,
                 f"{len(lines)} examples compared; schema-invalid but "
                 f"canonical-accepted: {bad or 'none'}",
                 [ev_stdout(run, art, "schema-agreement.txt")])
    sc.append(s.d)

    s = Scenario("evidence-content-required",
                 "a tested verdict whose evidence is an empty command "
                 "reference or an empty stdout entry is rejected",
                 fault_point="syntactically shaped but contentless evidence "
                 "passes as execution proof")
    runs = {}
    for name in ("err-command-empty.json", "err-stdout-empty.json"):
        runs[name] = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
                         str(ex_rel / name)])
    ok = all(r["exit_code"] == 2 for r in runs.values())
    s.tested(ok, runs["err-command-empty.json"],
             "; ".join(f"{n}: exit={r['exit_code']}" for n, r in runs.items()),
             [ev_stdout(runs["err-command-empty.json"], art,
                        "reject-empty-command.txt"),
              ev_stdout(runs["err-stdout-empty.json"], art,
                        "reject-empty-stdout.txt")])
    sc.append(s.d)

    s = Scenario("artifact-existence-verified",
                 "reports citing missing, escaped or digest-mismatched "
                 "artifact paths are rejected at validation time; the same "
                 "files pass structural validation with the artifact check "
                 "disabled, proving the rejection comes from artifact "
                 "verification",
                 fault_point="a fabricated digest on a nonexistent or "
                 "stale file is accepted as evidence")
    names = ("err-evidence-path-missing.json",
             "err-evidence-path-tampered.json",
             "err-artifacts-path-missing.json",
             "err-artifacts-path-escape.json")
    runs = {n: sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
                   str(ex_rel / n)]) for n in names}
    nocheck = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
                  "--no-artifact-check",
                  str(ex_rel / "err-evidence-path-tampered.json")])
    ok = all(r["exit_code"] == 2 for r in runs.values()) \
        and nocheck["exit_code"] == 0
    ev = [ev_stdout(r, art, f"reject-artifact-{n[4:-5]}.txt")
          for n, r in runs.items()]
    ev.append(ev_stdout(nocheck, art, "artifact-check-disabled.txt"))
    s.tested(ok, runs[names[0]],
             "; ".join(f"{n}: exit={r['exit_code']}" for n, r in runs.items())
             + f"; --no-artifact-check exit={nocheck['exit_code']} (0 shows "
               "the file is otherwise structurally valid)", ev)
    sc.append(s.d)

    s = Scenario("assurance-dimensions-explicit",
                 "a report without all six assurance dimensions or with a "
                 "passed/failed/warning state lacking a dimension-declaring "
                 "tested scenario is rejected; the valid example's "
                 "restore_test=passed is backed by a dimension-linked "
                 "tested-pass",
                 fault_point="an unchecked dimension is silently promoted "
                 "by an unrelated pass")
    names = ("err-assurance-missing.json", "err-assurance-incomplete.json",
             "err-assurance-unbacked.json", "err-dimensions-invalid.json")
    runs = {n: sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
                   str(ex_rel / n)]) for n in names}
    good = sh(["python3", str(VALIDATE.relative_to(REPO_ROOT)),
               str(ex_rel / "valid-report.json")])
    ok = all(r["exit_code"] == 2 for r in runs.values()) \
        and good["exit_code"] == 0
    ev = [ev_stdout(r, art, f"reject-{n[4:-5]}.txt") for n, r in runs.items()]
    ev.append(ev_stdout(good, art, "valid-assurance.txt"))
    s.tested(ok, runs[names[0]],
             "; ".join(f"{n}: exit={r['exit_code']}" for n, r in runs.items())
             + f"; valid-report exit={good['exit_code']}", ev)
    sc.append(s.d)

    return report, art


# ---------------------------------------------------------------- isolation

def copy_fixture(workdir, name="site-alpha"):
    """Ensure the fixture exists under lab-output and copy it into workdir."""
    src = LAB_OUT / "fixtures" / name
    if not src.exists():
        sh(["python3", str(GENERATE), "generate"])
    dest = Path(workdir) / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return dest


def build_rootfs(root):
    """Minimal read-only mount skeleton for the confined payload: only the
    bind-mount targets exist, so nothing outside them is even visible."""
    for d in ("usr", "bin", "lib", "lib64", "etc", "proc", "dev", "tmp",
              "site"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "etc" / "ld.so.cache").touch(exist_ok=True)


PAYLOAD_PREAMBLE = "WOV-PAYLOAD-START"
MARKER_ENV = "WOV_HOST_MARKER"


def run_isolation_payload(workdir):
    """Run restore_sim.py inside a narrowed bwrap namespace.

    Returns (run, result|None, started). `started` is False when the payload
    never emitted its preamble — a namespace/setup failure, which is a
    blocked prerequisite, not a demonstrated isolation result.
    """
    iso = Path(workdir) / "ns"
    site = copy_fixture(iso)
    shutil.copy2(PAYLOAD, site / "payload.py")
    rootfs = iso / "rootfs"
    build_rootfs(rootfs)
    sentinel = iso / "host-sentinel.txt"
    sentinel.write_text("host-only marker; must be unreadable inside the "
                        "namespace\n", encoding="utf-8")
    env = {**os.environ, MARKER_ENV: "wov-host-marker-value"}
    cmd = ["bwrap", "--unshare-all", "--die-with-parent",
           "--ro-bind", "rootfs", "/",
           "--ro-bind-try", "/usr", "/usr",
           "--ro-bind-try", "/bin", "/bin",
           "--ro-bind-try", "/lib", "/lib",
           "--ro-bind-try", "/lib64", "/lib64",
           "--ro-bind-try", "/etc/ld.so.cache", "/etc/ld.so.cache",
           "--proc", "/proc", "--dev", "/dev",
           "--bind", "site-alpha", "/site",
           "--chdir", "/site",
           "--clearenv",
           "--setenv", "PATH", "/usr/bin:/bin",
           "--setenv", "HOME", "/site",
           "/usr/bin/python3", "/site/payload.py",
           "--host-file", str(sentinel), "--marker-env", MARKER_ENV]
    run = sh(cmd, timeout=60, cwd=iso, env=env)
    out = run["stdout"] or ""
    started = out.startswith(PAYLOAD_PREAMBLE)
    body = out[len(PAYLOAD_PREAMBLE):] if started else ""
    try:
        return run, json.loads(body), started, sentinel
    except json.JSONDecodeError:
        return run, None, started, sentinel


def check_isolation(workdir, publish):
    report = base_report("g0-00-isolation-reset-canary",
                         ["VER-03", "NFR-02", "RST-08"], ["AC-26", "AC-33"])
    sc = report["scenarios"]
    art = Artifacts(Path(publish) / report["report_id"])

    probe = sh(["bwrap", "--version"], timeout=10)
    if probe["exit_code"] != 0:
        for sid in ("net-egress-denied", "fs-write-confined",
                    "namespace-confidentiality"):
            s = Scenario(sid, "namespace isolation is enforced")
            s.blocked("bwrap is not available in this environment")
            sc.append(s.d)
    else:
        payload_run, payload_result, started, sentinel = \
            run_isolation_payload(workdir)
        host_netns = os.readlink("/proc/self/ns/net")
        payload_ev = ev_stdout(payload_run, art, "payload-result.json",
                               "payload output inside the namespace")
        setup_blocker = None
        if not started:
            setup_blocker = (
                f"payload never started (bwrap exit "
                f"{payload_run['exit_code']}): the environment refused "
                f"namespace setup before the payload ran — "
                f"{payload_run['stderr'].strip()[:200] or 'no stderr'}. "
                "Not a demonstrated isolation result.")

        s = Scenario("net-egress-denied",
                     "payload attempts TCP egress to every lab role and "
                     "external SMTP/webhook stand-ins plus DNS resolution; "
                     "all must fail inside the isolated namespace",
                     fault_point="restored site tries to phone home (AC-26)")
        if setup_blocker:
            s.blocked(setup_blocker)
        elif payload_result is None:
            s.tested(False, payload_run,
                     "payload ran but produced no JSON result "
                     f"(exit={payload_run['exit_code']})",
                     [payload_ev])
        else:
            reached = [e for e in payload_result["egress"]
                       if e.get("reached") or e.get("resolved")]
            ns_differs = payload_result["netns"] != host_netns
            ok = not reached and ns_differs
            s.tested(ok, payload_run,
                     f"netns {payload_result['netns']} differs from host "
                     f"{host_netns}: {ns_differs}; egress successes={reached}",
                     [payload_ev])
        sc.append(s.d)

        s = Scenario("fs-write-confined",
                     "payload may write only inside its bound docroot; "
                     "writes to /, /etc, /usr, /tmp, /proc and via .. "
                     "traversal must fail against the read-only root "
                     "skeleton")
        if setup_blocker:
            s.blocked(setup_blocker)
        elif payload_result is None:
            s.tested(False, payload_run,
                     "payload ran but produced no JSON result",
                     [payload_ev])
        else:
            wrong = [w for w in payload_result["writes"]
                     if w["wrote"] != w["allowed"]]
            s.tested(not wrong, payload_run,
                     f"unexpected write outcomes={wrong}; "
                     f"attempts={[(w['path'], w['wrote']) for w in payload_result['writes']]}",
                     [payload_ev])
        sc.append(s.d)

        s = Scenario("namespace-confidentiality",
                     "the confined payload cannot see host files, harness "
                     "environment variables or host processes: the planted "
                     "sentinel and host files are unreadable, the marker "
                     "environment variable is absent, the PID namespace "
                     "shows only the sandbox's own processes and the "
                     "sentinel on the host is untouched afterwards",
                     fault_point="restored runtime reads host secrets, "
                     "environment or process table")
        if setup_blocker:
            s.blocked(setup_blocker)
        elif payload_result is None:
            s.tested(False, payload_run,
                     "payload ran but produced no JSON result",
                     [payload_ev])
        else:
            env_res = payload_result.get("env", {})
            procs = payload_result.get("procs", {})
            read_hits = [r for r in payload_result.get("reads", [])
                         if r.get("read")]
            sentinel_ok = sentinel.exists() and "host-only marker" in \
                sentinel.read_text(encoding="utf-8")
            iso_dir = Path(workdir) / "ns"
            inside = (iso_dir / "site-alpha", iso_dir / "rootfs")
            strays = [str(p.relative_to(iso_dir))
                      for p in iso_dir.rglob("*")
                      if p.is_file()
                      and all(r not in p.parents for r in inside)
                      and p != sentinel]
            ok = (not read_hits
                  and not env_res.get("marker_env_seen", True)
                  and not env_res.get("unexpected")
                  and not procs.get("beyond_sandbox")
                  and sentinel_ok
                  and not strays)
            s.tested(ok, payload_run,
                     f"host reads succeeded={read_hits}; "
                     f"marker_env_seen={env_res.get('marker_env_seen')}; "
                     f"unexpected env={env_res.get('unexpected')}; "
                     f"pids={procs.get('pids')}; "
                     f"sentinel intact={sentinel_ok}; strays={strays}",
                     [payload_ev])
        sc.append(s.d)

    # ---- baseline reset ------------------------------------------------
    s = Scenario("baseline-reset-restores",
                 "after mutation (modified, deleted and stray files), "
                 "labctl reset returns the working copy to the baseline")
    reset_ws = Path(workdir) / "reset"
    baseline = copy_fixture(reset_ws / "baseline")
    working = reset_ws / "working"
    shutil.copytree(baseline, working)
    (working / "htdocs" / "wp-config.php").write_text("<?php // tampered\n")
    (working / "db" / "dump.sql").unlink()
    (working / "stray-dir").mkdir()
    (working / "stray-dir" / "stray.txt").write_text("stray\n")
    run = sh(["python3", str(LABCTL), "reset", "--scope", str(working),
              "--baseline", str(baseline)])
    try:
        outcome = json.loads(run["stdout"])
    except json.JSONDecodeError:
        outcome = {}
    same = outcome.get("matches_baseline") is True
    s.tested(run["exit_code"] == 0 and same, run,
             f"reset exit={run['exit_code']}; matches_baseline={same}; "
             f"removed={outcome.get('removed_strays')}",
             [ev_stdout(run, art, "reset.json")])
    sc.append(s.d)

    s = Scenario("reset-refuses-unowned",
                 "labctl reset refuses a scope outside task-owned prefixes")
    run = sh(["python3", str(LABCTL), "reset", "--scope", "docs",
              "--baseline", str(baseline)])
    s.tested(run["exit_code"] == 3, run,
             f"reset exit={run['exit_code']} (3=refused): {run['stderr'].strip()}",
             [ev_stdout(run, art, "reset-refuse.txt")])
    sc.append(s.d)

    s = Scenario("reset-refuses-overlap",
                 "reset refuses scope/baseline pairs where one contains the "
                 "other, so it cannot destroy the baseline it restores from")
    ov = Path(workdir) / "overlap"
    (ov / "base").mkdir(parents=True, exist_ok=True)
    ov_rel = ov.relative_to(REPO_ROOT)
    runs = {
        "base-in-scope": sh(["python3", str(LABCTL), "reset",
                             "--scope", str(ov_rel),
                             "--baseline", str(ov_rel / "base")]),
        "scope-in-base": sh(["python3", str(LABCTL), "reset",
                             "--scope", str(ov_rel / "base"),
                             "--baseline", str(ov_rel)]),
    }
    ok = all(r["exit_code"] == 3 for r in runs.values()) and (ov / "base").is_dir()
    s.tested(ok, runs["base-in-scope"],
             "; ".join(f"{k}: exit={r['exit_code']} (3=refused)"
                       for k, r in runs.items()),
             [ev_stdout(runs["base-in-scope"], art,
                        "reset-overlap-refuse.txt"),
              ev_stdout(runs["scope-in-base"], art,
                        "reset-overlap-refuse-rev.txt")])
    sc.append(s.d)

    # ---- canary redaction ----------------------------------------------
    can_ws = Path(workdir) / "canary"
    can_ws.mkdir(parents=True, exist_ok=True)
    pins = json.loads(PINS_PATH.read_text())
    canaries = {c["id"]: c["value"] for c in pins["canaries"]}
    raw = can_ws / "job.raw.log"
    raw.write_text(
        "2026-11-04T12:00:00Z job start\n"
        f"connect db host=localhost password={canaries['db-password']}\n"
        f"mysqldump -u wp -p{canaries['db-password']} wp_alpha\n"
        f"PUT https://storage.example.test/auth token={canaries['external-writer-token']}\n"
        f"smtp login smtp.example.test pass={canaries['smtp-credential']}\n"
        "2026-11-04T12:00:03Z job done\n", encoding="utf-8")

    s = Scenario("canary-leak-detected",
                 "the canary scanner flags every pinned canary in a raw "
                 "artifact (detector proves it can see leaks)")
    run = sh(["python3", str(LABCTL), "scan", "--paths", str(raw)])
    found = set()
    errors = ["unparseable"]
    try:
        doc = json.loads(run["stdout"])
        found = {h["canary_id"] for h in doc["hits"]}
        errors = doc.get("errors", [])
    except json.JSONDecodeError:
        pass
    ok = run["exit_code"] == 1 and found == set(canaries) and not errors
    s.tested(ok, run, f"scan exit={run['exit_code']}; detected ids={sorted(found)}",
             [ev_stdout(run, art, "scan-raw.json")])
    sc.append(s.d)

    s = Scenario("canary-redaction",
                 "the sanitized copy of the same artifact contains no canary "
                 "value (AC-33: canaries absent from publishable artifacts)")
    sanitized = can_ws / "job.sanitized.log"
    red = sh(["python3", str(LABCTL), "redact", "--in", str(raw),
              "--out", str(sanitized)])
    run = sh(["python3", str(LABCTL), "scan", "--paths", str(sanitized)])
    ok = run["exit_code"] == 0 and red["exit_code"] == 0
    saved = art.save("job.sanitized.log", sanitized.read_bytes())
    ev = [ev_stdout(run, art, "scan-sanitized.json"),
          art.evidence(saved, "sanitized artifact")]
    s.tested(ok, run, f"redact exit={red['exit_code']}; "
             f"sanitized scan exit={run['exit_code']} (0=clean)",
             ev)
    sc.append(s.d)

    s = Scenario("scan-incomplete-coverage",
                 "the scanner never reports clean on incomplete coverage: "
                 "a missing path, an unreadable file and a binary file "
                 "carrying canary bytes are each handled explicitly",
                 fault_point="missing or undecodable input silently passes "
                 "as a clean scan")
    probes = {}
    probes["missing-path"] = sh(
        ["python3", str(LABCTL), "scan", "--paths",
         str(can_ws / "does-not-exist.log")])
    unreadable = can_ws / "unreadable.log"
    unreadable.write_text(canaries["db-password"] + "\n")
    unreadable.chmod(0)
    probes["unreadable"] = sh(
        ["python3", str(LABCTL), "scan", "--paths", str(unreadable)])
    binary = can_ws / "blob.bin"
    binary.write_bytes(b"\x00\xff\x89binary" +
                       canaries["smtp-credential"].encode() + b"\x00\xfe")
    probes["binary-canary"] = sh(
        ["python3", str(LABCTL), "scan", "--paths", str(binary)])
    (can_ws / "clean").mkdir(exist_ok=True)
    (can_ws / "clean" / "ok.txt").write_text("no tokens\n")
    probes["clean-dir"] = sh(
        ["python3", str(LABCTL), "scan", "--paths", str(can_ws / "clean")])
    try:
        bin_doc = json.loads(probes["binary-canary"]["stdout"])
        bin_hit = any(h["canary_id"] == "smtp-credential"
                      for h in bin_doc["hits"])
    except json.JSONDecodeError:
        bin_hit = False
    ok = (probes["missing-path"]["exit_code"] == 2
          and probes["unreadable"]["exit_code"] == 2
          and probes["binary-canary"]["exit_code"] == 1 and bin_hit
          and probes["clean-dir"]["exit_code"] == 0)
    ev = [ev_stdout(probes[k], art, f"scan-coverage-{k}.json")
          for k in probes]
    s.tested(ok, probes["missing-path"],
             "; ".join(f"{k}: exit={r['exit_code']}" for k, r in probes.items())
             + f"; binary canary hit={bin_hit}", ev)
    sc.append(s.d)

    s = Scenario("reports-carry-no-canary",
                 "committed evidence and run artifacts reference canaries by "
                 "id only; no canary value appears under lab/evidence/ "
                 "(the report file itself is written after this scan and "
                 "contains ids only; it is covered by the post-run rescan)")
    run = sh(["python3", str(LABCTL), "scan", "--paths", str(LAB / "evidence")])
    try:
        doc = json.loads(run["stdout"])
        hits, errors = doc["hits"], doc.get("errors", [])
    except json.JSONDecodeError:
        hits, errors = [{"error": "unparseable"}], ["unparseable"]
    s.tested(run["exit_code"] == 0 and not hits and not errors, run,
             f"scan exit={run['exit_code']}; hits={hits}; errors={errors}",
             [ev_stdout(run, art, "scan-reports.json")])
    sc.append(s.d)

    s = Scenario("no-workstation-paths-in-evidence",
                 "no retained artifact under lab/evidence/ contains the "
                 "absolute repository or home path — evidence is "
                 "repository-relative and sanitized before publication")
    probe_start = time.monotonic()
    probe_ran_at = utcnow()
    needles = (str(REPO_ROOT).encode(), str(Path.home()).encode())
    offenders = []
    for f in sorted((LAB / "evidence").rglob("*")):
        if not f.is_file():
            continue
        data = f.read_bytes()
        for n in needles:
            if n in data:
                offenders.append(rel(f))
                break
    run = {"exit_code": 0 if not offenders else 1,
           "stdout": f"absolute-path offenders={offenders}\n",
           "stderr": "", "ran_at": probe_ran_at,
           "duration_ms": round((time.monotonic() - probe_start) * 1000, 1)}
    s.tested(not offenders, run,
             f"files containing workstation-absolute prefixes: {offenders}",
             [ev_stdout(run, art, "workstation-path-scan.txt")])
    sc.append(s.d)

    s = Scenario("container-isolation-profile",
                 "the same isolation checks execute inside wov-g000-* "
                 "containers on the coordinator profile")
    s.blocked("no Docker socket in this environment; container profile is "
              "coordinator-run and must produce its own run evidence")
    sc.append(s.d)

    return report, art


GROUPS = {
    "targets": check_targets,
    "fixtures": check_fixtures,
    "schema": check_schema,
    "isolation": check_isolation,
}


def resolve_publish(path):
    """--publish must stay inside the retained-evidence directory; evidence
    publication is scoped separately from the disposable workdir."""
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    p = p.resolve()
    # Compare against the lexical root: resolving an owned root would grant
    # ownership to the target of a symlink replacing that root or an ancestor.
    base = Path(os.path.abspath(PUBLISH_DIR))
    if p == base or base in p.parents:
        return p
    raise labctl.Refused(f"--publish {path} resolves outside "
                         f"{PUBLISH_DIR.relative_to(REPO_ROOT)}")


def cleanup_for(gdir_rel, no_cleanup):
    """Run (or explicitly skip) cleanup of one group's workdir and return the
    report block. Runs on success, failure and exception paths alike."""
    if no_cleanup:
        return {"performed": False, "verified": False, "ran_at": utcnow(),
                "resources_removed": [], "refused": [],
                "leftovers": [f"{gdir_rel} retained intentionally "
                              "(--no-cleanup)"]}
    run = sh(["python3", str(LABCTL), "cleanup", "--apply",
              "--path", gdir_rel])
    try:
        cres = json.loads(run["stdout"])
    except json.JSONDecodeError:
        cres = {"performed": False, "verified": False,
                "leftovers": [f"{gdir_rel} cleanup output unparseable "
                              f"(exit {run['exit_code']})"]}
    return {"performed": cres.get("performed", False),
            "verified": cres.get("verified", False),
            "ran_at": utcnow(),
            "resources_removed": cres.get("resources_removed", []),
            "refused": cres.get("refused", []),
            "leftovers": cres.get("leftovers", [])}


def harness_failure_report(name, exc, publish):
    """A group that crashed before producing its report still gets a valid
    blocked report — an honest 'not run' outcome, never a silent gap."""
    report = base_report(f"g0-00-{name}-harness-error", ["NFR-02"], ["AC-33"])
    art = Artifacts(Path(publish) / report["report_id"])
    tb = art.save("traceback.txt", traceback.format_exc())
    s = Scenario("group-executed", "the check group runs to completion")
    s.d["verdict"] = "blocked"
    s.d["blocker"] = (f"harness exception {type(exc).__name__}: {exc}; "
                      "the group's scenarios did not run")
    s.d["evidence"] = [art.evidence(tb)]
    report["scenarios"] = [s.d]
    return report, art


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=list(GROUPS) + ["all"])
    parser.add_argument("--workdir", type=Path,
                        default=LAB_OUT / "runs" / datetime.now(timezone.utc)
                        .strftime("%Y%m%dT%H%M%S%fZ"))
    parser.add_argument("--publish", type=Path, default=PUBLISH_DIR)
    parser.add_argument("--no-cleanup", action="store_true",
                        help="retain each group's workdir (recorded in the "
                             "report's cleanup block)")
    args = parser.parse_args(argv)

    try:
        workdir = labctl.resolve_owned(args.workdir)
        publish = resolve_publish(args.publish)
    except labctl.Refused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return 3
    publish.mkdir(parents=True, exist_ok=True)
    try:
        # A reused workspace could contain redirected group or payload paths.
        # Refuse it intact instead of trusting or deleting its descendants.
        workdir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("REFUSED --workdir must name a new workspace; existing data "
              "is preserved", file=sys.stderr)
        return 3

    names = list(GROUPS) if args.group == "all" else [args.group]
    results, failures = {}, []
    for name in names:
        gdir = workdir / name
        try:
            gdir = labctl.resolve_owned(gdir)
            gdir.mkdir(parents=True, exist_ok=False)
            report, art = GROUPS[name](gdir, publish)
        except Exception as exc:  # never leave a group without a report
            traceback.print_exc()
            report, art = harness_failure_report(name, exc, publish)
            failures.append(name)
        gdir_rel = str(gdir.relative_to(REPO_ROOT))
        cleanup_block = cleanup_for(gdir_rel, args.no_cleanup)
        path, ok = finalize(report, art, publish, cleanup_block)
        results[name] = (path, ok)
        counts = evidence_validate.verdict_summary(report)
        print(f"{name}: {'VALID' if ok else 'INVALID'} -> {path}")
        print("  verdicts: " + "  ".join(f"{k}={v}" for k, v in counts.items() if v))
        if counts.get("tested-fail"):
            failures.append(f"{name}(tested-fail)")

    if not args.no_cleanup and workdir.exists():
        # Groups removed their own subdirs; drop the now-empty run root.
        left = sorted(str(p.relative_to(workdir)) for p in workdir.rglob("*"))
        if not left:
            workdir.rmdir()
        else:
            print(f"note: run workdir retains {left}", file=sys.stderr)

    bad = not all(ok for _, ok in results.values())
    if bad or failures:
        print(f"FAILED: {failures or 'invalid report(s)'}", file=sys.stderr)
        return 1
    print("all groups: valid reports, no tested-fail outcomes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
