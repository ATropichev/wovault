F1 (blocking): `lab/tools/run_checks.py:1188–1191` validates the workdir but passes unchecked child directories to mutating checks. If `<workdir>/targets` already symlinks to `docs/`, `check_targets` creates directories and symlinks there; isolation helpers similarly write beneath unchecked descendants. This violates acceptance criterion 1’s disposable-resource boundary and the template’s symlink confinement promise. A read-only mocked-resolution probe confirmed the callback receives the escaped directory while `resolve_owned` rejects that same path. Validate group and nested destinations before mutation.

A1 (advisory): `lab/evidence/report.schema.json:150` accepts contentless stdout evidence, although the canonical validator rejects it. The differential check on `err-stdout-empty.json` returned zero schema errors and one canonical error. Add the content requirement to the published schema.

Acceptance coverage: Criterion 1 has explicit targets, budgets and cleanup plans; `verify-allowlist` passes, and a simulated symlink replacing the owned root is refused, but F1 prevents full acceptance. Criterion 2 has pinned synthetic inputs and manifests; `generate.py --check` matches all three fixtures. Criterion 3 is demonstrated by the 25-example validator self-test and unknown-state examples, subject to A1. Criterion 4 has retained isolation/reset/canary run artifacts; all four reports validate with artifact hashes checked. Those experiments were not rerun during this read-only review.

The supplied diff stays within `lab/` and `docs/research/` and implements group 1 without selecting engines or completing G0. Retained-artifact scans found no pinned canaries or matching private-home paths/private-key markers; absolute `/tmp` matches describe synthetic probes. No CI or gate success is established.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "e3481d7b85d369711169564e00d19e9bef788a19",
  "verdict": "changes_required",
  "findings": ["F1"],
  "advisory_findings": ["A1"],
  "classes": {
    "F1": "security",
    "A1": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {"what": "python3 -B lab/evidence/validate.py --selftest", "result": "25 examples behaved as expected"},
      {"what": "python3 -B lab/tools/labctl.py verify-allowlist", "result": "Passed; only local-sandbox executable"},
      {"what": "python3 -B lab/fixtures/generate.py --check", "result": "All three pinned manifests matched"},
      {"what": "python3 -B lab/tools/labctl.py scan --paths lab/evidence", "result": "85 files; zero hits or coverage errors"},
      {"what": "In-memory validation of all four retained report JSON files", "result": "All valid with artifact existence and digest verification"},
      {"what": "Read-only mocked Path.resolve probe of runner group dispatch", "result": "Escaped group directory reached callback; resolve_owned rejected the same directory"},
      {"what": "Read-only mocked owned-root symlink probe", "result": "resolve_owned refused"},
      {"what": "JSON Schema versus canonical validation of err-stdout-empty.json", "result": "Schema accepted; canonical rejected"},
      {"what": "rg scan of retained artifacts for home/workstation paths and selected secret markers", "result": "Only synthetic /tmp probe paths matched"},
      {"what": "scripts/check", "result": "Could not run checks: pinned tooling unavailable; requested setup-tools"},
      {"what": "git rev-parse HEAD and git status --short", "result": "Unavailable: snapshot has no Git repository metadata"}
    ],
    "read": [
      "README.md",
      "docs/PRD.md",
      "docs/research/landscape.md",
      "docs/roadmap.md",
      "docs/threat-model.md",
      "docs/implementation-plan.md",
      "docs/research/experiment-template.md",
      "docs/development.md",
      "docs/agent-workflow.md",
      "openspec/changes/validate-g0-feasibility/proposal.md",
      "openspec/changes/validate-g0-feasibility/design.md",
      "openspec/changes/validate-g0-feasibility/tasks.md",
      "openspec/changes/validate-g0-feasibility/specs/feasibility-evidence/spec.md",
      "openspec/specs/ (only .gitkeep)",
      "Supplied contract and diff",
      "scripts/setup-tools",
      "scripts/check"
    ],
    "not_run": [
      {"what": "scripts/setup-tools", "why": "Installs files; incompatible with read-only review"},
      {"what": "Full lab runner and publication unittest suite", "why": "Create or modify files"},
      {"what": "Remote/container experiments", "why": "No authorization; unnecessary for this review"},
      {"what": "CI and AgentMarshal gate", "why": "No SHA-bound result supplied and required tooling unavailable"}
    ]
  },
  "evidence": {
    "F1": "lab/tools/run_checks.py:1188; unchecked gdir dispatched at line 1191; mutating check_targets uses workdir/symlink-check. Mocked probe printed 'group callback received: lab-output/review/targets resolved: docs'; resolve_owned returned Refused.",
    "A1": "lab/evidence/report.schema.json:150; differential check printed 'empty stdout: schema errors= 0 canonical errors= 1'."
  }
}
AGENTMARSHAL_VERDICT_END
