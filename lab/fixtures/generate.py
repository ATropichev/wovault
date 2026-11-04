#!/usr/bin/env python3
"""Deterministic synthetic-site fixture generator for the G0 lab.

Generates the fixture trees pinned in lab/fixtures/pins.json under
lab-output/fixtures/<name>/ plus <name>.manifest.json next to each tree.
All bytes derive from the pinned seed via SHA-256 counter mode; generation
contains no randomness, wall-clock time or host-dependent data, so repeated
runs must produce identical manifests.

Usage:
    generate.py generate [--out DIR] [--name FIXTURE]
    generate.py --check [--expected DIR]
    generate.py --write-expected [--expected DIR]   # bootstrap the pinned manifests
"""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PINS_PATH = Path(__file__).resolve().parent / "pins.json"
DEFAULT_OUT = REPO_ROOT / "lab-output" / "fixtures"
DEFAULT_EXPECTED = Path(__file__).resolve().parent / "expected"

sys.path.insert(0, str(REPO_ROOT / "lab" / "tools"))
sys.dont_write_bytecode = True  # keep the import from leaving __pycache__ in the repo
import labctl  # noqa: E402


def resolve_under(path, base):
    """Resolve PATH to a real path inside BASE, or raise labctl.Refused.

    Like labctl.resolve_owned but against an explicit base: the resolved path
    (symlinks and '..' included) must stay inside the resolved base."""
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    p = p.resolve()
    b = Path(base).resolve()
    if p == b or b in p.parents:
        return p
    raise labctl.Refused(f"{path} resolves outside {Path(base).resolve()}")


def load_pins(path=PINS_PATH):
    with open(path, "r", encoding="utf-8") as fh:
        pins = json.load(fh)
    for fx in pins["fixtures"]:
        spec_ids = {c["id"] for c in pins["canaries"]}
        unknown = set(fx.get("canary_ids", [])) - spec_ids
        if unknown:
            raise ValueError(f"{fx['name']}: unknown canary ids {sorted(unknown)}")
    return pins


def stream(seed, key, nbytes):
    """Deterministic byte stream: SHA-256(seed|key|counter) counter mode."""
    out = bytearray()
    counter = 0
    while len(out) < nbytes:
        out += hashlib.sha256(f"{seed}|{key}|{counter}".encode("utf-8")).digest()
        counter += 1
    return bytes(out[:nbytes])


def hextoken(seed, key, length=12):
    return stream(seed, key, (length + 1) // 2).hex()[:length]


def canary_map(pins):
    return {c["id"]: c["value"] for c in pins["canaries"]}


def build_site(spec, pins):
    """Return {relative_path: bytes} for one fixture site."""
    seed = pins["seed"]
    name = spec["name"]
    vers = pins["simulated_versions"]
    canaries = canary_map(pins)
    files = {}

    def put(path, text):
        files[path] = text.encode("utf-8")

    put("site.json", json.dumps({
        "fixture": name,
        "fixture_spec": pins["fixture_spec"],
        "synthetic": True,
        "role": spec["role"],
        "domain": spec["domain"],
        "doc_address": spec["doc_address"],
        "db_name": spec["db_name"],
        "db_prefix": spec["db_prefix"],
        "simulated_versions": vers,
    }, indent=2, sort_keys=True) + "\n")

    db_password = canaries.get("db-password") if "db-password" in spec.get("canary_ids", []) \
        else f"synthetic-db-pw-{hextoken(seed, name + '/dbpw')}"
    put("htdocs/wp-config.php", "\n".join([
        "<?php",
        f"// Synthetic fixture config for {name}; never a real credential.",
        f"define('DB_NAME', '{spec['db_name']}');",
        "define('DB_USER', 'wp_fixture_user');",
        f"define('DB_PASSWORD', '{db_password}');",
        "define('DB_HOST', 'localhost');",
        f"define('AUTH_KEY', 'synthetic-{hextoken(seed, name + '/auth')}');",
        f"define('SECURE_AUTH_KEY', 'synthetic-{hextoken(seed, name + '/sauth')}');",
        f"$table_prefix = '{spec['db_prefix']}';",
        "",
    ]))
    put("htdocs/index.php", "<?php\n// Synthetic WordPress front controller stub.\nrequire __DIR__ . '/wp-includes/version.php';\n")
    put("htdocs/wp-includes/version.php",
        f"<?php\n// Synthetic version stamp.\n$wp_version = '{vers['wordpress']}';\n")
    put("htdocs/wp-admin/admin.php", "<?php\n// Synthetic wp-admin entry stub.\n")

    for plugin in spec["plugins"]:
        base = f"htdocs/wp-content/plugins/{plugin}"
        put(f"{base}/{plugin}.php", "\n".join([
            "<?php",
            f"// Plugin Name: {plugin} (synthetic stub)",
            f"// X-Simulated-Version: {vers.get(plugin.replace('-', '_'), vers['wordpress'])}",
            f"// Content-Id: {hextoken(seed, base)}",
            "",
        ]))
        put(f"{base}/readme.txt",
            f"=== {plugin} ===\nSynthetic fixture stub; pinned body {hextoken(seed, base + '/readme', 16)}.\n")

    for mu in spec["mu_plugins"]:
        put(f"htdocs/wp-content/mu-plugins/{mu}.php",
            f"<?php\n// Synthetic MU plugin {mu}; id {hextoken(seed, name + '/mu/' + mu)}.\n")

    put(f"htdocs/wp-content/themes/{spec['theme']}/style.css",
        f"/*\nTheme Name: {spec['theme']} (synthetic)\nId: {hextoken(seed, name + '/theme')}\n*/\n")

    put("htdocs/wp-content/uploads/.htaccess",
        "# Synthetic uploads policy\nphp_flag engine off\n")
    for i in range(spec["upload_files"]):
        body = stream(seed, f"{name}/uploads/{i}", 96).hex()
        put(f"htdocs/wp-content/uploads/2026/10/file-{i:02d}.txt",
            f"synthetic-upload {name} {i}\n{body}\n")
    put("htdocs/wp-content/cache/object/probe.cache",
        f"synthetic cache blob {hextoken(seed, name + '/cache')}\n")

    put("db/dump.sql", build_dump(spec, pins))

    put("writers/cron.log", "".join(
        f"2026-10-31T00:{i:02d}:00Z CRON {name} {spec['db_prefix']}scheduled_action_{i} status=ok\n"
        for i in range(6)))
    if "queue" in spec["writers"]:
        put("writers/queue.state", json.dumps({
            "queue": f"{name}-jobs",
            "pending": [f"job-{hextoken(seed, f'{name}/q/{i}', 8)}" for i in range(3)],
            "processed": 128 + spec["woo_orders"],
        }, indent=2, sort_keys=True) + "\n")
    if "external-importer" in spec["writers"]:
        token = canaries.get("external-writer-token", f"synthetic-{hextoken(seed, name + '/ext')}")
        put("writers/external-importer.conf", "\n".join([
            "# Synthetic 1C-style importer writer config",
            f"endpoint = https://importer.example.test/{name}",
            f"token = {token}",
            "interval_seconds = 900",
            "",
        ]))
    if "smtp-credential" in spec.get("canary_ids", []):
        put("writers/smtp.conf", "\n".join([
            "# Synthetic outbound mail writer config",
            f"host = smtp.example.test",
            f"password = {canaries['smtp-credential']}",
            "",
        ]))

    if "registry-domain-mismatch" in spec["drift"]:
        put("drift/registry-vs-vhost.json", json.dumps({
            "note": "synthetic REG-03 drift fixture",
            "registry_domains": [f"old-{spec['domain']}"],
            "vhost_server_names": [spec["domain"], f"www.{spec['domain']}"],
            "vhost_aliases_unregistered": [f"www.{spec['domain']}"] if "vhost-alias-unregistered" in spec["drift"] else [],
            "expected": "inventory reports a coverage gap; no hidden repair",
        }, indent=2, sort_keys=True) + "\n")
    return files


def build_dump(spec, pins):
    seed = pins["seed"]
    name = spec["name"]
    pfx = spec["db_prefix"]
    canaries = canary_map(pins)
    lines = [
        "-- Synthetic database dump; contains no real data.",
        f"-- fixture={name} spec={pins['fixture_spec']}",
        f"CREATE TABLE `{pfx}options` (`option_name` varchar(64), `option_value` text);",
        f"INSERT INTO `{pfx}options` VALUES ('siteurl','https://{spec['domain']}'),('home','https://{spec['domain']}'),('blogname','{name} synthetic');",
    ]
    if "smtp-credential" in spec.get("canary_ids", []):
        lines.append(
            f"INSERT INTO `{pfx}options` VALUES ('smtp_password','{canaries['smtp-credential']}');")
    lines.append(
        f"CREATE TABLE `{pfx}posts` (`ID` int, `post_title` text, `post_status` varchar(20));")
    for i in range(5):
        lines.append(
            f"INSERT INTO `{pfx}posts` VALUES ({100 + i},'synthetic post {i}','publish');")
    if spec["woo_orders"]:
        lines += [
            f"CREATE TABLE `{pfx}wc_orders` (`id` int, `email` text, `total` decimal(8,2), `status` varchar(20));",
        ]
        for i in range(spec["woo_orders"]):
            oid = 1000 + i
            email = f"customer{i}@example.com"
            total = f"{19 + (i % 7)}.{(i * 37) % 100:02d}"
            status = "completed" if i % 5 else "processing"
            lines.append(
                f"INSERT INTO `{pfx}wc_orders` VALUES ({oid},'{email}',{total},'{status}');")
    lines.append("")
    return "\n".join(lines)


def manifest_for(name, files, pins, pins_sha):
    entries = [
        {"path": p, "sha256": hashlib.sha256(b).hexdigest(), "size": len(b), "mode": "0644"}
        for p, b in sorted(files.items())
    ]
    canon = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "fixture": name,
        "fixture_spec": pins["fixture_spec"],
        "seed": pins["seed"],
        "pins_sha256": pins_sha,
        "synthetic": True,
        "files": entries,
        "manifest_digest": hashlib.sha256(canon).hexdigest(),
    }


def write_tree(root, files):
    for rel, body in files.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        dest.chmod(0o644)


def cmd_generate(pins, out_dir, only=None):
    pins_sha = hashlib.sha256(PINS_PATH.read_bytes()).hexdigest()
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for spec in pins["fixtures"]:
        if only and spec["name"] != only:
            continue
        files = build_site(spec, pins)
        tree = out_dir / spec["name"]
        if tree.is_symlink():
            raise labctl.Refused(f"{tree} is a symlink; refusing to generate into it")
        if tree.exists():
            shutil.rmtree(tree)
        write_tree(tree, files)
        manifest = manifest_for(spec["name"], files, pins, pins_sha)
        mpath = out_dir / f"{spec['name']}.manifest.json"
        if mpath.is_symlink():
            mpath.unlink()
        mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append((spec["name"], manifest["manifest_digest"], len(files)))
    return results


def regenerate_manifest(spec, pins):
    return manifest_for(spec["name"], build_site(spec, pins), pins,
                        hashlib.sha256(PINS_PATH.read_bytes()).hexdigest())


def cmd_check(pins, expected_dir):
    ok = True
    for spec in pins["fixtures"]:
        epath = expected_dir / f"{spec['name']}.manifest.json"
        if not epath.exists():
            print(f"MISSING expected manifest: {epath}", file=sys.stderr)
            ok = False
            continue
        expected = json.loads(epath.read_text(encoding="utf-8"))
        actual = regenerate_manifest(spec, pins)
        match = expected["files"] == actual["files"] and \
            expected["manifest_digest"] == actual["manifest_digest"] and \
            expected["seed"] == actual["seed"]
        status = "MATCH" if match else "MISMATCH"
        if not match:
            ok = False
        print(f"{status} {spec['name']} digest={actual['manifest_digest']}")
    return ok


def cmd_write_expected(pins, expected_dir):
    expected_dir.mkdir(parents=True, exist_ok=True)
    for spec in pins["fixtures"]:
        manifest = regenerate_manifest(spec, pins)
        (expected_dir / f"{spec['name']}.manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"pinned {spec['name']} digest={manifest['manifest_digest']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="generate", choices=["generate"])
    parser.add_argument("--check", action="store_true", help="compare regenerated manifests to pinned expected ones")
    parser.add_argument("--write-expected", action="store_true", help="(re)write pinned expected manifests")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--name", default=None)
    args = parser.parse_args(argv)

    pins = load_pins()
    try:
        # Generation deletes and rewrites <out>/<fixture>; the destination must
        # resolve inside a task-owned prefix before any mutation, and the pinned
        # manifests may only be rewritten inside lab/fixtures/expected/.
        out = labctl.resolve_owned(args.out) if not (args.check or args.write_expected) else None
        if args.check:
            return 0 if cmd_check(pins, args.expected) else 1
        if args.write_expected:
            cmd_write_expected(pins, resolve_under(args.expected, DEFAULT_EXPECTED))
            return 0
        for name, digest, count in cmd_generate(pins, out, args.name):
            print(f"generated {name} files={count} digest={digest}")
        return 0
    except labctl.Refused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
