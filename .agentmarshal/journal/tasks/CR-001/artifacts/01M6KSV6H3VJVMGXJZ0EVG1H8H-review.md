F1 — Blocking, security: `lab/tools/run_checks.py:1104` resolves the publication root before comparing ownership. If `lab/evidence/runs/` itself is a symlink outside the repository, `resolve_publish()` accepts its destination. Artifact and report writes then occur before validation (`:116`, `:215`). A read-only mocked-symlink probe confirmed acceptance. This violates NFR-02’s symlink-escape defense and the named experiment template’s scope boundary. The disposable `lab-output/` root correctly refuses the equivalent case.

F2 — Blocking, contract-mismatch: `lab/tools/run_checks.py:1143` copies exception text into report blockers, and `:215` publishes reports without sanitization. An in-memory `OSError` containing the repository’s absolute path retained that path in the report and passed structural validation. This violates the named experiment template’s prohibition on workstation-private paths in public artifacts. The inspected retained artifacts contain no workstation/home prefixes or canary values; the defect concerns newly generated error reports.

A1 — Advisory, correctness: `lab/evidence/validate.py:233` performs set membership before checking the profile’s type. Setting `executor.profile` to `{}` raises `TypeError` instead of returning validation errors. Across 584 in-memory mutations, no schema-invalid report was accepted, but 41 cases raised exceptions.

Acceptance criterion 1 is substantially implemented by `lab/targets.json`, `lab/resources.json` and `lab/topology.md`; `verify-allowlist` passed, and mocked container cleanup removed only the prefixed container while preserving the unrelated one. F1 prevents full acceptance of the ownership boundary.

Acceptance criterion 2 is met by `lab/fixtures/pins.json`, the generator and expected manifests. `generate.py --check` matched all three pinned manifests; retained repeatability evidence also passed digest verification.

Acceptance criterion 3 is met for the supplied examples: validator selftest passed 25/25, unknown remains separate from tested-pass, and all four retained reports validated with artifact checks. Published-schema comparison found no schema-invalid example accepted by the canonical validator. A1 identifies additional malformed-input handling to improve.

Acceptance criterion 4 has retained run evidence in `g0-00-isolation-reset-canary.json`, including namespace denials, baseline reset and canary detection/redaction; its referenced artifacts passed digest checks. These experiments were not rerun in this read-only review. Container isolation remains explicitly blocked.

The supplied diff stays within `lab/` and `docs/research/`, implements group 1 only, and makes no final engine or supported-version decision. All named documents were inspected; `openspec/specs/` contains no specification files. No files were changed or production accessed. No CI success or independent reproduction of the historical runs is asserted.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8694288c6f79ae9a7e141815e8e3b4ef923e1ddb",
  "verdict": "changes_required",
  "findings": ["F1", "F2"],
  "advisory_findings": ["A1"],
  "classes": {
    "F1": "security",
    "F2": "contract-mismatch",
    "A1": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "pwd; git rev-parse HEAD; git status --short",
        "result": "Workspace path confirmed; Git commands failed because the snapshot has no Git repository. Commit identity could not be independently verified."
      },
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
        "result": "Passed; local-sandbox executable, container and VPS profiles pending."
      },
      {
        "what": "python3 -B lab/tools/labctl.py scan --paths lab/evidence",
        "result": "85 files scanned; zero hits, zero errors, complete coverage."
      },
      {
        "what": "In-memory validation of all four retained reports with target and artifact existence/digest checks",
        "result": "All valid; totals agree with 33 tested-pass and one blocked scenario."
      },
      {
        "what": "jsonschema Draft202012Validator.check_schema and comparison of all 25 example reports",
        "result": "Schema valid; no schema-invalid example accepted by canonical validator."
      },
      {
        "what": "584 in-memory field-type mutations of valid-report.json",
        "result": "No schema-invalid report accepted; 41 validator exceptions."
      },
      {
        "what": "Read-only mocked publication-root and disposable-root symlink probes",
        "result": "Publication-root escape accepted; disposable-root escape refused."
      },
      {
        "what": "Intercepted artifact/report writes and in-memory harness exception report generation",
        "result": "Artifact writes lack resolved destination checks; error report retained absolute repository prefix and passed structural validation. No writes reached disk."
      },
      {
        "what": "Mocked activated-container cleanup with unrelated-site and wov-g000-source",
        "result": "Only wov-g000-source received docker rm; unrelated-site was preserved. No Docker daemon contacted."
      },
      {
        "what": "rg scan of retained evidence for home, workstation, temporary paths and credential-related text",
        "result": "Inspected matches were synthetic probe paths, sandbox paths, canary IDs and redacted values; no workstation/home prefixes or credentials identified."
      },
      {
        "what": "scripts/check",
        "result": "Stopped at missing pinned AgentMarshal executable; public checks did not complete."
      },
      {
        "what": "agentmarshal brief --task CR-001 with repository scripts PATH and AGENTMARSHAL_ACTOR=agent-codex",
        "result": "Could not execute brief: pinned AgentMarshal installation absent."
      }
    ],
    "read": [
      "Supplied CR-001 contract and diff",
      "README.md",
      "docs/PRD.md",
      "docs/research/landscape.md",
      "docs/roadmap.md",
      "docs/threat-model.md",
      "docs/implementation-plan.md",
      "docs/research/experiment-template.md",
      "docs/research/g0-00-lab-and-evidence-protocol.md",
      "docs/development.md",
      "docs/agent-workflow.md",
      "openspec/changes/validate-g0-feasibility/proposal.md",
      "openspec/changes/validate-g0-feasibility/design.md",
      "openspec/changes/validate-g0-feasibility/tasks.md",
      "openspec/changes/validate-g0-feasibility/specs/feasibility-evidence/spec.md",
      "openspec/specs/ directory listing",
      "Lab tooling, schema, fixtures, configuration, documentation and retained evidence supplied in the diff",
      "scripts/check, scripts/setup-tools, scripts/agentmarshal and scripts/openspec"
    ],
    "not_run": [
      {
        "what": "scripts/setup-tools",
        "why": "Installs dependencies and modifies files; prohibited by this read-only assignment."
      },
      {
        "what": "run_checks.py all, fixture generation, reset and filesystem cleanup experiments",
        "why": "Require filesystem mutations; retained evidence was inspected instead."
      },
      {
        "what": "Live container or remote-VPS experiments",
        "why": "Not authorized; container cleanup was checked using mocked subprocess calls only."
      },
      {
        "what": "SHA-bound CI and AgentMarshal gate",
        "why": "No actual SHA-bound CI result supplied; pinned governance tools and Git metadata absent."
      }
    ]
  },
  "evidence": {
    "F1": "lab/tools/run_checks.py:1104 resolves PUBLISH_DIR itself; mocked root symlink probe returned publish root symlink modeled: True. Writes at :116 and :215 precede artifact validation.",
    "F2": "lab/tools/run_checks.py:1143 embeds raw exception text; :215 writes unsanitized report JSON. In-memory probe: error blocker retains repository prefix: True; structural validation of error report: [].",
    "A1": "lab/evidence/validate.py:233; in-memory executor.profile={} probe raised TypeError: unhashable type: 'dict'."
  }
}
AGENTMARSHAL_VERDICT_END
