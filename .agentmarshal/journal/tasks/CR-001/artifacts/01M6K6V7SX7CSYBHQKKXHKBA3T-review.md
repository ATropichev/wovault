Changes are required. The supplied diff stays within `lab/` and `docs/research/`, implements only G0 group 1, and leaves architecture and supported versions undecided.

- Acceptance 1: `targets.json`, `resources.json` and `topology.md` define disposable targets, limits and cleanup. Allowlist verification passes, but F1 breaks ownership enforcement.
- Acceptance 2: pinned synthetic fixtures and manifests exist. `generate.py --check` matches all three fixtures; retained repeatability evidence is present.
- Acceptance 3: all nine validator examples pass their expected outcomes, including rejection of missing fields and tested-pass without execution evidence. Unknown counts as zero passes. However, F2 demonstrates disagreement with the published schema.
- Acceptance 4: retained isolation, reset, canary and cleanup evidence exists; all 24 artifact digests match. My canary scan found zero hits in 39 files. Runtime isolation was not independently rerun, and container results remain explicitly blocked.

F1 — **Blocking, security:** `lab/tools/labctl.py:55–64` resolves both the requested path and the owned root. If `lab-output` is a symlink to an unrelated directory, that directory becomes “owned,” allowing reset/cleanup outside the intended workspace. A read-only mocked-resolution test confirmed acceptance of the unrelated root and its children. This violates acceptance 1’s disposable-resource boundary and NFR-02’s symlink-escape protection.

F2 — **Blocking, contract-mismatch:** `lab/evidence/validate.py` accepts reports rejected by its published schema: `artifacts={}`, integer target roles, integer blocker descriptions, null tools, and malformed stdout digests. Five in-memory differential tests against `Draft202012Validator` confirmed these discrepancies. Acceptance 3 and task 1.3 require a coherent machine-readable evidence contract.

F3 — **Blocking, claim-accuracy:** `lab/tools/labctl.py:263–270` ignores container-removal failures and reports `verified=true`, an empty leftovers list, and exit 0. A mocked Docker removal returning exit 1 reproduced this false cleanup confirmation. This violates group 1.4’s requirement to retain actual cleanup results. The same test confirmed that the unrelated container was not removed.

A1 — **Advisory, security:** six retained schema-check artifacts disclose an absolute workstation path, starting at `lab/evidence/runs/g0-00-evidence-schema/reject-missing.txt:1`. Public-artifact sanitization should replace these with repository-relative paths; the canary scan does not detect this metadata leak.

A2 — **Advisory, correctness:** `lab/tools/labctl.py:194–197` deletes the scope before copying the baseline without rejecting overlapping paths. A mocked reset with its baseline beneath the scope confirmed that deletion precedes reading the now-deleted baseline. No files were deleted during review.

A3 — **Advisory, claim-accuracy:** `lab/tools/run_checks.py:356,386` assigns `duration_ms=1.0` rather than measuring the two fixture checks. The report presents these fields as measured durations; they should be measured or explicitly identified as placeholders.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "774d5bc966b26833cc21616a03a7733ee23977e6",
  "verdict": "changes_required",
  "findings": ["F1", "F2", "F3"],
  "advisory_findings": ["A1", "A2", "A3"],
  "classes": {
    "F1": "security",
    "F2": "contract-mismatch",
    "F3": "claim-accuracy",
    "A1": "security",
    "A2": "correctness",
    "A3": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {
        "what": "python3 lab/evidence/validate.py --selftest",
        "result": "All nine examples produced their expected acceptance or rejection."
      },
      {
        "what": "python3 lab/fixtures/generate.py --check",
        "result": "All three pinned manifests matched."
      },
      {
        "what": "python3 lab/tools/labctl.py verify-allowlist --json",
        "result": "Only local-sandbox executable; two pending targets; zero errors."
      },
      {
        "what": "python3 lab/tools/labctl.py scan --paths lab/evidence",
        "result": "39 files scanned; zero canary hits."
      },
      {
        "what": "In-memory validation of four retained reports and SHA-256 verification of their artifact lists",
        "result": "Four reports valid; all 24 artifact digests matched."
      },
      {
        "what": "Draft202012Validator.check_schema and validation of four retained reports",
        "result": "Schema syntax valid; all four retained reports valid."
      },
      {
        "what": "Five in-memory differential schema/validator negative tests",
        "result": "Canonical validator accepted all five malformed variants; published schema rejected each."
      },
      {
        "what": "Mocked Path.resolve test of a symlinked owned root",
        "result": "Unrelated root and children accepted as owned; no filesystem changes."
      },
      {
        "what": "Mocked overlapping reset",
        "result": "Scope deletion called before copying its nested baseline; no filesystem changes."
      },
      {
        "what": "Mocked Docker enumeration and failed removal",
        "result": "Failed removal reported as verified success; unrelated container received no removal call."
      },
      {
        "what": "rg search for absolute paths in retained artifacts",
        "result": "Six schema-check artifacts contain absolute workstation paths."
      },
      {
        "what": "PATH=\"$PWD/scripts:$PATH\" AGENTMARSHAL_ACTOR=agent-codex scripts/check",
        "result": "Could not proceed: pinned AgentMarshal executable absent; wrapper requested setup."
      },
      {
        "what": "git rev-parse HEAD; git status --short; git show --stat --oneline HEAD",
        "result": "Unavailable: snapshot has no Git repository metadata; supplied SHA not independently confirmed."
      }
    ],
    "read": [
      "Supplied CR-001 contract and diff",
      "AGENTS.md",
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
      "openspec/specs/ contains only .gitkeep",
      "Candidate lab tooling, configuration, fixtures, schema, examples, retained evidence and research report",
      "scripts/check, scripts/setup-tools and pinned CLI wrappers"
    ],
    "not_run": [
      {
        "what": "scripts/setup-tools",
        "why": "Installs files; review is read-only."
      },
      {
        "what": "Full run_checks suite, fixture tree generation and real reset/cleanup",
        "why": "Write artifacts or remove resources; review is read-only."
      },
      {
        "what": "Real container or remote execution",
        "why": "No container or remote operations authorized for this review."
      },
      {
        "what": "SHA-bound CI and AgentMarshal gate",
        "why": "No actual candidate-bound CI result supplied; pinned tooling unavailable."
      }
    ]
  },
  "evidence": {
    "F1": "lab/tools/labctl.py:55-64; mocked symlink resolution accepted /synthetic-unrelated and /synthetic-unrelated/important.",
    "F2": "lab/evidence/validate.py:95-112,170-173,281-291; five differential tests returned zero canonical errors while Draft202012Validator rejected every variant.",
    "F3": "lab/tools/labctl.py:263-270; mocked docker rm returned 1 but output reported verified=true, resources_removed=[wov-g000-source], leftovers=[], exit 0.",
    "A1": "lab/evidence/runs/g0-00-evidence-schema/reject-missing.txt:1 and five sibling artifacts contain absolute workstation paths.",
    "A2": "lab/tools/labctl.py:194-197; mocked calls delete lab-output before copying lab-output/baseline.",
    "A3": "lab/tools/run_checks.py:356,386; both duration_ms fields are hardcoded to 1.0."
  }
}
AGENTMARSHAL_VERDICT_END
