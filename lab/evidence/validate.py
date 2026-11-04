#!/usr/bin/env python3
"""Validate G0 evidence reports against lab/evidence/report.schema.json.

Canonical implementation of the schema contract, written against the Python
standard library only so the lab has no third-party dependency. Besides field
shape it enforces the evidence rules that matter for acceptance:

  * required fields and closed objects (unknown keys are rejected);
  * verdicts tested-pass/tested-fail require a real run record
    (actual{summary,exit_code,ran_at,duration_ms} plus at least one evidence
    entry; file/log evidence needs a sha256 digest);
  * verdicts planned/documented/blocked/unknown must NOT carry run results —
    an unknown or blocked scenario can never present itself as executed;
  * blocked requires a blocker, documented requires a source;
  * every evidence entry carries verifiable content: file/log/digest need a
    sha256, command/stdout need a non-empty note, and any recorded path needs
    a sha256 — an empty reference is not evidence;
  * every recorded path must be repository-relative, exist and match its
    declared sha256 (disable with --no-artifact-check); missing, escaped or
    tampered artifacts invalidate the report;
  * all six assurance dimensions are declared explicitly; a state of
    passed/failed/warning requires a tested-* scenario whose dimensions
    declare that key (passed needs tested-pass) — not_checked/unsupported
    are always honest;
  * --targets cross-checks that the named target is authorized in the
    executable allowlist (lab/targets.json).

Validation confirms structure and that referenced evidence files exist and
match their digests; it does not by itself prove the recorded runs were
honest — a fabricated artifact with a matching digest still fails
verification only when its content or digest disagrees with what is on disk.

Exit codes: 0 valid, 2 invalid report, 1 usage/IO error.
Usage:
    validate.py REPORT.json [--targets lab/targets.json] [--summary]
    validate.py --selftest
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SCHEMA_PATH = HERE / "report.schema.json"
DEFAULT_TARGETS = REPO_ROOT / "lab" / "targets.json"

VERDICTS = {"planned", "documented", "tested-pass", "tested-fail", "blocked", "unknown"}
TESTED = {"tested-pass", "tested-fail"}
NON_TESTED = {"planned", "documented", "blocked", "unknown"}
ASSURANCE_KEYS = {"transfer", "completeness", "consistency", "integrity", "restore_test", "security"}
ASSURANCE_STATES = {"passed", "failed", "warning", "not_checked", "unsupported"}
TARGET_KINDS = {"local-namespace", "container-set", "remote-vps"}
PROFILES = TARGET_KINDS
EVIDENCE_KINDS = {"file", "log", "stdout", "digest", "command"}

RE_REPORT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
RE_SCENARIO_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
RE_TASK = re.compile(r"^CR-[0-9]+$")
RE_AC = re.compile(r"^AC-[0-9]{2}$")
RE_REQ = re.compile(r"^(S[1-6]|(REG|BKP|STO|VER|SEC|RST|UI|NFR)-[0-9]{2})$")
RE_SHA = re.compile(r"^[0-9a-f]{64}$")
RE_UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


class Report:
    def __init__(self):
        self.errors = []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")


def is_utc_z(value):
    if not isinstance(value, str) or not RE_UTC.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return True
    except ValueError:
        return False


def check_no_extra(obj, allowed, where, rep):
    for key in obj:
        if key not in allowed:
            rep.err(where, f"unexpected key '{key}'")


def check_measurements(items, where, rep):
    if not isinstance(items, list):
        rep.err(where, "measurements must be an array")
        return
    for i, m in enumerate(items):
        w = f"{where}[{i}]"
        if not isinstance(m, dict):
            rep.err(w, "measurement must be an object")
            continue
        check_no_extra(m, {"name", "value", "unit", "conditions"}, w, rep)
        for k in ("name", "unit"):
            if not isinstance(m.get(k), str) or not m[k]:
                rep.err(w, f"'{k}' must be a non-empty string")
        if not isinstance(m.get("value"), (int, float)) or isinstance(m.get("value"), bool):
            rep.err(w, "'value' must be a number")
        if "conditions" in m and not isinstance(m["conditions"], str):
            rep.err(w, "'conditions' must be a string")


def check_evidence(items, where, rep):
    if not isinstance(items, list):
        rep.err(where, "evidence must be an array")
        return
    for i, e in enumerate(items):
        w = f"{where}[{i}]"
        if not isinstance(e, dict):
            rep.err(w, "evidence entry must be an object")
            continue
        check_no_extra(e, {"kind", "path", "sha256", "note"}, w, rep)
        kind = e.get("kind")
        if not isinstance(kind, str) or kind not in EVIDENCE_KINDS:
            rep.err(w, f"kind must be one of {sorted(EVIDENCE_KINDS)}")
            continue
            kind = None
        if "path" in e and not (isinstance(e["path"], str) and e["path"]):
            rep.err(w, "path must be a non-empty string")
        if "sha256" in e and not (isinstance(e["sha256"], str)
                                and RE_SHA.match(e["sha256"])):
            rep.err(w, "sha256 must be 64 hex chars")
        if "note" in e and not isinstance(e["note"], str):
            rep.err(w, "note must be a string")
        if "path" in e and "sha256" not in e:
            rep.err(w, "a recorded path requires a sha256 digest")
        if kind in {"file", "log", "digest"} and not e.get("sha256"):
            rep.err(w, f"kind '{kind}' requires a sha256 digest")
        if kind in {"file", "log"} and not e.get("path"):
            rep.err(w, f"kind '{kind}' requires path")
        note_ok = isinstance(e.get("note"), str) and bool(e["note"].strip())
        if kind == "command" and not note_ok:
            rep.err(w, "kind 'command' requires a non-empty note; "
                       "an empty command reference is not evidence")
        if kind == "stdout" and not (note_ok or (e.get("path") and e.get("sha256"))):
            rep.err(w, "kind 'stdout' requires a non-empty note or a "
                       "digested artifact path; an empty reference is not evidence")


def check_actual(actual, where, rep):
    if not isinstance(actual, dict):
        rep.err(where, "actual must be an object")
        return
    check_no_extra(actual, {"summary", "exit_code", "ran_at", "duration_ms"}, where, rep)
    if not isinstance(actual.get("summary"), str) or not actual["summary"]:
        rep.err(where, "actual.summary must be a non-empty string")
    if not isinstance(actual.get("exit_code"), int) or isinstance(actual.get("exit_code"), bool):
        rep.err(where, "actual.exit_code must be an integer")
    if not is_utc_z(actual.get("ran_at")):
        rep.err(where, "actual.ran_at must be an ISO-8601 UTC time ending in Z")
    dur = actual.get("duration_ms")
    if not isinstance(dur, (int, float)) or isinstance(dur, bool) or dur < 0:
        rep.err(where, "actual.duration_ms must be a number >= 0")


def check_scenario(s, i, rep):
    where = f"scenarios[{i}]"
    if not isinstance(s, dict):
        rep.err(where, "scenario must be an object")
        return
    allowed = {"id", "title", "expected", "fault_point", "verdict", "actual",
               "evidence", "blocker", "source", "measurements", "dimensions"}
    check_no_extra(s, allowed, where, rep)
    sid = s.get("id")
    if not (isinstance(sid, str) and RE_SCENARIO_ID.match(sid)):
        rep.err(where, "id must match ^[a-z0-9][a-z0-9-]{1,63}$")
        sid = f"#{i}"
    w = f"scenario '{sid}'"
    if not isinstance(s.get("expected"), str) or not s["expected"]:
        rep.err(w, "expected must be a non-empty string")
    for k in ("title", "fault_point"):
        if k in s and not isinstance(s[k], str):
            rep.err(w, f"'{k}' must be a string")
    for k in ("blocker", "source"):
        if k in s and not (isinstance(s[k], str) and s[k]):
            rep.err(w, f"'{k}' must be a non-empty string")
    verdict = s.get("verdict")
    if verdict is None:
        rep.err(w, "missing required field 'verdict'")
        return
    if not isinstance(verdict, str) or verdict not in VERDICTS:
        rep.err(w, f"verdict '{verdict}' is not one of {sorted(VERDICTS)}")
        return
    has_actual = "actual" in s
    if verdict in TESTED:
        if not has_actual:
            rep.err(w, f"verdict '{verdict}' requires an actual run record")
        else:
            check_actual(s["actual"], w + ".actual", rep)
        ev = s.get("evidence")
        if not isinstance(ev, list) or len(ev) < 1:
            rep.err(w, f"verdict '{verdict}' requires at least one evidence entry")
        else:
            check_evidence(ev, w + ".evidence", rep)
    else:
        if has_actual:
            rep.err(w, f"verdict '{verdict}' must not carry an actual run record; "
                       "non-tested outcomes are not executions")
        if "evidence" in s:
            check_evidence(s["evidence"], w + ".evidence", rep)
    if verdict == "blocked" and not s.get("blocker"):
        rep.err(w, "verdict 'blocked' requires a blocker description")
    if verdict == "documented" and not s.get("source"):
        rep.err(w, "verdict 'documented' requires a source")
    if "measurements" in s:
        check_measurements(s["measurements"], w + ".measurements", rep)
    if "dimensions" in s:
        dims = s["dimensions"]
        if not (isinstance(dims, list) and dims):
            rep.err(w, "dimensions must be a non-empty array of assurance keys")
        else:
            for i, d in enumerate(dims):
                if not isinstance(d, str) or d not in ASSURANCE_KEYS:
                    rep.err(w, f"dimensions[{i}] '{d}' is not an assurance key")


def check_executor(ex, rep):
    w = "executor"
    if not isinstance(ex, dict):
        rep.err(w, "must be an object")
        return
    check_no_extra(ex, {"actor", "profile", "environment"}, w, rep)
    if not isinstance(ex.get("actor"), str) or not ex["actor"]:
        rep.err(w, "actor must be a non-empty string")
    if not isinstance(ex.get("profile"), str) or ex["profile"] not in PROFILES:
        rep.err(w, f"profile must be one of {sorted(PROFILES)}")
    env = ex.get("environment")
    if not isinstance(env, dict):
        rep.err(w + ".environment", "must be an object")
    else:
        check_no_extra(env, {"os", "arch", "kernel", "python", "tools"}, w + ".environment", rep)
        for k in ("os", "arch"):
            if not isinstance(env.get(k), str) or not env[k]:
                rep.err(w + ".environment", f"'{k}' must be a non-empty string")
        for k in ("kernel", "python"):
            if k in env and not isinstance(env[k], str):
                rep.err(w + ".environment", f"'{k}' must be a string")
        if "tools" in env and not (
                isinstance(env["tools"], dict) and all(
                    isinstance(v, str) for v in env["tools"].values())):
            rep.err(w + ".environment.tools", "must be an object of string values")


def check_target(t, rep, targets_doc):
    w = "target"
    if not isinstance(t, dict):
        rep.err(w, "must be an object")
        return
    check_no_extra(t, {"name", "kind", "authorized", "roles"}, w, rep)
    if not isinstance(t.get("name"), str) or not t["name"]:
        rep.err(w, "name must be a non-empty string")
    if not isinstance(t.get("kind"), str) or t["kind"] not in TARGET_KINDS:
        rep.err(w, f"kind must be one of {sorted(TARGET_KINDS)}")
    if t.get("authorized") is not True:
        rep.err(w, "authorized must be true; unauthorized targets cannot produce evidence")
    if "roles" in t and not (isinstance(t["roles"], list) and all(
            isinstance(x, str) for x in t["roles"])):
        rep.err(w, "roles must be an array of strings")
    if targets_doc is not None and isinstance(t.get("name"), str):
        allowed = {x["name"] for x in targets_doc.get("targets", []) if x.get("authorized")}
        if t["name"] not in allowed:
            rep.err(w, f"name '{t['name']}' is not an authorized target in the allowlist")


def check_assurance(a, dim_tested, dim_passed, rep):
    """All six dimensions must be declared; a checked state needs a tested-*
    scenario that declares the same dimension in its 'dimensions' field, so a
    generic pass can never silently promote an unchecked dimension."""
    w = "assurance"
    if not isinstance(a, dict):
        rep.err(w, "must be an object")
        return
    for k, v in a.items():
        if k not in ASSURANCE_KEYS:
            rep.err(w, f"unexpected assurance key '{k}'")
        elif not isinstance(v, str) or v not in ASSURANCE_STATES:
            rep.err(w, f"'{k}' must be one of {sorted(ASSURANCE_STATES)}")
    missing = sorted(ASSURANCE_KEYS - set(a))
    if missing:
        rep.err(w, f"must declare all six dimensions explicitly; "
                   f"missing: {missing}")
    for k, v in a.items():
        if k not in ASSURANCE_KEYS or not isinstance(v, str):
            continue
        if v == "passed" and k not in dim_passed:
            rep.err(w, f"'{k}'=passed requires a tested-pass scenario "
                       f"declaring dimensions containing '{k}'")
        elif v in {"failed", "warning"} and k not in dim_tested:
            rep.err(w, f"'{k}'={v} requires a tested-* scenario "
                       f"declaring dimensions containing '{k}'")


def verify_artifact_paths(doc, rep, root=REPO_ROOT):
    """Check that every recorded path is repository-relative, exists inside
    the repository and matches its declared sha256. A syntactically valid
    digest naming a missing, escaped or tampered file is not evidence."""
    def check_path(value, sha, where):
        p = Path(value)
        if p.is_absolute():
            rep.err(where, "path must be repository-relative, not absolute")
            return
        resolved = (root / p).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            rep.err(where, f"path '{value}' escapes the repository")
            return
        if not resolved.is_file():
            rep.err(where, f"artifact '{value}' does not exist")
            return
        if sha and hashlib.sha256(resolved.read_bytes()).hexdigest() != sha:
            rep.err(where, f"artifact '{value}' sha256 does not match "
                           "the recorded digest")

    for i, s in enumerate(doc.get("scenarios") or []):
        if not isinstance(s, dict):
            continue
        for j, e in enumerate(s.get("evidence") or []):
            if isinstance(e, dict) and e.get("path"):
                check_path(e["path"], e.get("sha256"),
                           f"scenarios[{i}].evidence[{j}]")
    for i, a in enumerate(doc.get("artifacts") or []):
        if isinstance(a, dict) and a.get("path"):
            check_path(a["path"], a.get("sha256"), f"artifacts[{i}]")


def validate(doc, targets_doc=None, verify_artifacts=True):
    rep = Report()
    if not isinstance(doc, dict):
        rep.err("$", "report must be a JSON object")
        return rep
    allowed = {"schema_version", "report_id", "task", "change", "generated_at",
               "executor", "target", "requirement_ids", "ac_ids", "scenarios",
               "assurance", "measurements", "artifacts", "cleanup", "notes"}
    check_no_extra(doc, allowed, "$", rep)
    required = ["schema_version", "report_id", "task", "change", "generated_at",
                "executor", "target", "requirement_ids", "ac_ids", "scenarios",
                "assurance"]
    for field in required:
        if field not in doc:
            rep.err("$", f"missing required field '{field}'")
    if doc.get("schema_version") != "g0-evidence/1":
        rep.err("schema_version", "must be 'g0-evidence/1'")
    if not (isinstance(doc.get("report_id"), str) and RE_REPORT_ID.match(doc["report_id"])):
        rep.err("report_id", "must match ^[a-z0-9][a-z0-9-]{2,63}$")
    if not (isinstance(doc.get("task"), str) and RE_TASK.match(doc["task"])):
        rep.err("task", "must match ^CR-[0-9]+$")
    if not isinstance(doc.get("change"), str) or not doc.get("change", ""):
        rep.err("change", "must be a non-empty string")
    if not is_utc_z(doc.get("generated_at")):
        rep.err("generated_at", "must be an ISO-8601 UTC time ending in Z")
    if "executor" in doc:
        check_executor(doc["executor"], rep)
    if "target" in doc:
        check_target(doc["target"], rep, targets_doc)
    for key, rx in (("requirement_ids", RE_REQ), ("ac_ids", RE_AC)):
        ids = doc.get(key)
        if not isinstance(ids, list):
            rep.err(key, "must be an array")
        else:
            for i, v in enumerate(ids):
                if not (isinstance(v, str) and rx.match(v)):
                    rep.err(f"{key}[{i}]", f"invalid id '{v}'")
    scenarios = doc.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        rep.err("scenarios", "must be a non-empty array")
        scenarios = []
    for i, s in enumerate(scenarios):
        check_scenario(s, i, rep)
    dim_tested, dim_passed = set(), set()
    for s in scenarios:
        if not isinstance(s, dict):
            continue
        raw_dims = s.get("dimensions")
        dims = {d for d in raw_dims if isinstance(d, str) and d in ASSURANCE_KEYS} \
            if isinstance(raw_dims, list) else set()
        if isinstance(s.get("verdict"), str) and s["verdict"] in TESTED:
            dim_tested |= dims
        if s.get("verdict") == "tested-pass":
            dim_passed |= dims
    if "assurance" in doc:
        check_assurance(doc["assurance"], dim_tested, dim_passed, rep)
    if "measurements" in doc:
        check_measurements(doc["measurements"], "measurements", rep)
    if "artifacts" in doc:
        if not isinstance(doc["artifacts"], list):
            rep.err("artifacts", "must be an array")
        else:
            for i, a in enumerate(doc["artifacts"]):
                w = f"artifacts[{i}]"
                if not isinstance(a, dict):
                    rep.err(w, "must be an object")
                    continue
                check_no_extra(a, {"path", "sha256", "note"}, w, rep)
                if not isinstance(a.get("path"), str) or not a["path"]:
                    rep.err(w, "path must be a non-empty string")
                if not (isinstance(a.get("sha256"), str) and RE_SHA.match(a["sha256"])):
                    rep.err(w, "sha256 must be 64 hex chars")
                if "note" in a and not isinstance(a["note"], str):
                    rep.err(w, "note must be a string")
    if "notes" in doc and not isinstance(doc["notes"], str):
        rep.err("notes", "must be a string")
    if "cleanup" in doc:
        c = doc["cleanup"]
        w = "cleanup"
        if not isinstance(c, dict):
            rep.err(w, "must be an object")
        else:
            check_no_extra(c, {"performed", "verified", "ran_at",
                               "resources_removed", "refused", "leftovers"}, w, rep)
            for k in ("performed", "verified"):
                if not isinstance(c.get(k), bool):
                    rep.err(w, f"'{k}' must be a boolean")
            if "ran_at" in c and not is_utc_z(c["ran_at"]):
                rep.err(w, "ran_at must be an ISO-8601 UTC time ending in Z")
            for k in ("resources_removed", "refused", "leftovers"):
                if k in c and not (isinstance(c[k], list) and all(isinstance(x, str) for x in c[k])):
                    rep.err(w, f"'{k}' must be an array of strings")
    if verify_artifacts and not rep.errors:
        verify_artifact_paths(doc, rep)
    return rep


def verdict_summary(doc):
    counts = {v: 0 for v in sorted(VERDICTS)}
    for s in doc.get("scenarios", []):
        if isinstance(s, dict) and isinstance(s.get("verdict"), str) and s["verdict"] in counts:
            counts[s["verdict"]] += 1
    return counts


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def selftest(examples_dir, targets_doc):
    """Validate every example: valid-* must pass, err-* must fail."""
    ok = True
    for path in sorted(examples_dir.glob("*.json")):
        doc = load_json(path)
        rep = validate(doc, targets_doc, verify_artifacts=True)
        expect_valid = path.name.startswith("valid-")
        passed = not rep.errors
        status = "OK" if passed == expect_valid else "SELFTEST-FAIL"
        if passed != expect_valid:
            ok = False
        detail = "valid" if passed else f"{len(rep.errors)} error(s)"
        print(f"{status} {path.name}: {detail}")
    return ok


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS,
                        help="executable allowlist for target cross-check")
    parser.add_argument("--no-targets", action="store_true")
    parser.add_argument("--no-artifact-check", action="store_true",
                        help="skip existence/digest verification of recorded "
                             "paths (structural check only)")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    targets_doc = None
    if not args.no_targets:
        try:
            targets_doc = load_json(args.targets)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"cannot load targets allowlist {args.targets}: {exc}", file=sys.stderr)
            return 1
    if args.selftest:
        return 0 if selftest(HERE / "examples", targets_doc) else 2
    if args.report is None:
        parser.error("a report path is required unless --selftest")

    try:
        doc = load_json(args.report)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID {args.report}: cannot load JSON: {exc}", file=sys.stderr)
        return 1
    rep = validate(doc, targets_doc, verify_artifacts=not args.no_artifact_check)
    if rep.errors:
        print(f"INVALID {args.report}")
        for e in rep.errors:
            print(f"  - {e}")
        return 2
    print(f"VALID {args.report}")
    if args.summary:
        counts = verdict_summary(doc)
        print("  verdicts: " + "  ".join(f"{k}={v}" for k, v in counts.items() if v))
        print(f"  tested-pass scenarios: {counts['tested-pass']} of {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
