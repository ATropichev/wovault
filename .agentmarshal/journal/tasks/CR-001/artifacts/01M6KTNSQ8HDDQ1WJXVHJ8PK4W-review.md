No blocking defects found in the supplied candidate.

- Acceptance 1: `lab/targets.json`, `resources.json` and `topology.md` define disposable targets, limits and cleanup. Allowlist verification passed. Read-only mocked checks confirmed symlink-root refusal and reset overlap refusal without mutation.
- Acceptance 2: pinned synthetic inputs and manifests exist; `generate.py --check` matched all three fixtures.
- Acceptance 3: validator self-tests and both malformed-report tests passed. A 792-mutation differential check found no schema-invalid report accepted by the canonical validator.
- Acceptance 4: retained isolation, reset and canary reports contain run records and artifacts whose hashes validate. These experiments were not rerun here.

The supplied diff stays within the contract’s scope and group 1. Referenced OpenSpec documents preserve later G0 work and proposed architecture decisions. Public-artifact inspection found no workstation-private paths or apparent credentials; `/tmp` references identify synthetic refusal probes.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "c0151409d384c04c5d55870e7afd69271aceea1e",
  "verdict": "approved",
  "findings": [],
  "verification": {
    "executed": [
      {
        "what": "python3 -B lab/evidence/validate.py --selftest",
        "result": "Passed all 25 examples."
      },
      {
        "what": "python3 -B lab/fixtures/generate.py --check",
        "result": "All three pinned manifests matched."
      },
      {
        "what": "python3 -B lab/tools/labctl.py verify-allowlist",
        "result": "Passed; local-sandbox executable, both other profiles pending."
      },
      {
        "what": "python3 -B lab/tools/labctl.py scan --paths lab/evidence",
        "result": "85 files scanned; zero hits or errors."
      },
      {
        "what": "Python read-only validation of all four lab/evidence/runs/*.json reports",
        "result": "All valid; referenced artifact existence and SHA-256 hashes verified."
      },
      {
        "what": "Python unittest execution of MalformedReportTests",
        "result": "Both tests passed."
      },
      {
        "what": "Python schema/canonical differential check over 792 field-type mutations",
        "result": "Zero schema-invalid reports accepted by the canonical validator."
      },
      {
        "what": "Python mocked path-resolution and reset refusal checks",
        "result": "Owned-root, child and publication-root symlink escapes refused; unowned and overlapping reset paths returned 3 with zero mutation calls."
      },
      {
        "what": "rg inspection of retained public artifacts for private absolute paths and common credential markers",
        "result": "Only synthetic /tmp probe references matched."
      },
      {
        "what": "PATH=\"$PWD/scripts:$PATH\" AGENTMARSHAL_ACTOR=agent-codex scripts/check",
        "result": "Could not complete: pinned AgentMarshal installation absent. This is not a candidate check failure."
      },
      {
        "what": "git rev-parse HEAD",
        "result": "Unavailable: snapshot has no Git metadata; SHA association comes from the supplied review assignment."
      }
    ],
    "read": [
      "Supplied contract and diff",
      "README.md",
      "docs/PRD.md",
      "docs/research/landscape.md",
      "docs/roadmap.md",
      "docs/threat-model.md",
      "docs/implementation-plan.md",
      "docs/development.md",
      "docs/agent-workflow.md",
      "docs/decisions/0001-scope-and-engines.md",
      "docs/research/experiment-template.md",
      "docs/research/g0-00-lab-and-evidence-protocol.md",
      "openspec/changes/validate-g0-feasibility/",
      "openspec/specs/ (empty except .gitkeep)",
      ".agentmarshal/extensions/openspec.toml",
      "lab documentation, configuration, generator, validator, runner, payload, tests and retained evidence",
      "scripts/check, scripts/setup-tools and CLI wrappers"
    ],
    "not_run": [
      {
        "what": "scripts/setup-tools",
        "why": "Would modify files; review is read-only."
      },
      {
        "what": "Full publication tests and run_checks.py all",
        "why": "Create temporary workspaces or publish artifacts; prohibited by the read-only review."
      },
      {
        "what": "Container, remote-VPS, CI and AgentMarshal gate verification",
        "why": "No authorized execution environment or actual SHA-bound CI/gate result supplied; no success claimed."
      }
    ]
  }
}
AGENTMARSHAL_VERDICT_END
