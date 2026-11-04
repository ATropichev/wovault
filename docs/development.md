# Development environment and change governance

Date: 2026-11-04. These are development tools, not an installed WOVault application.

## Installation

Requires Git ≥2.31, Python ≥3.12, Node ≥22.12 and uv. From the checkout root:

```sh
scripts/setup-tools
export PATH="$PWD/scripts:$PATH"
export AGENTMARSHAL_ACTOR=agent-codex
agentmarshal doctor
scripts/check
```

AgentMarshal **0.6.0** is installed in `.venv`; OpenSpec **1.15.0** in
`tools/openspec/node_modules`. OpenSpec dependencies are pinned in package-lock.json.
This intentionally matches the [AgentMarshal v0.6.0 integration](https://github.com/agentmarshal/agentmarshal/blob/v0.6.0/.agentmarshal/extensions/openspec.toml),
not a claim to use latest. Update the pin, lock, extension manifest and generated
skills together. Global installations, Codex settings and sandbox permissions are
unchanged. OpenSpec telemetry is disabled in the wrapper and CI. Wrappers preserve
the current working directory.

In this environment, the working root is a nested Git checkout; enter it first.
Codex instructions live in AGENTS.md and generated `.agents/skills/openspec-*`.
The contributor-facing contract, review and evidence workflow is documented in
[Agent workflow](agent-workflow.md). No model provider account or agent launcher
is required to run the public checks.
If the current interface has not discovered the new skills, the CLI and AGENTS.md
are immediately available; reopen the project to select skills normally.

## Sources of truth

- `docs/PRD.md`: product requirements and IDs; `docs/roadmap.md`: gates and AC-01–35.
- `docs/implementation-plan.md`: work order, dependencies and G0 decision conditions.
- `openspec/changes/validate-g0-feasibility/`: the active G0 validation plan.
- `openspec/specs/`: accepted specifications; empty until the first delta is accepted.
- `.agentmarshal/journal/`: contracts, check references and review results.

An OpenSpec delta does not mean a feature is implemented. Task checkboxes represent
completed, verified work; proposal/design files only establish planning readiness.
After G0, record the adopt/integrate/build outcome in a separate ADR decision.

## Documentation language

English is the authoritative language for public documentation, ADRs, research
summaries, OpenSpec proposals/specifications/designs/tasks and AgentMarshal CR
contracts and acceptance criteria. Keep requirement IDs, scenario IDs, commands,
paths and machine-readable status values stable when translating. Any secondary
translation is non-authoritative and may be updated as needed. Documentation language
does not change the PRD's English/Russian product-UI requirement.

## AgentMarshal and OpenSpec integration

`.agentmarshal/extensions/openspec.toml` is a declarative schema-1 extension.
AgentMarshal includes its documents in briefs and its footprint in a contract's
effective scope. The extension does not execute OpenSpec or verify requirement
semantics; `scripts/check`, CI and the reviewer do that. Because `extensions`
expands scope to the entire footprint, review must also check that edits belong
to the assigned change.

Single-task contract template (save to a temporary file outside the journal):

```toml
+++
schema = 2
id = "CR-000"
title = "G0: reproducible WordOps inventory experiment"
scope = ["lab/", "docs/research/"]
acceptance = ["REG-03 / AC-03: inventory does not execute site PHP; evidence names exact versions"]
documents = ["docs/PRD.md", "docs/implementation-plan.md", "openspec/changes/validate-g0-feasibility/"]
extensions = ["openspec"]
+++

Implement only the assigned experiment on explicitly authorized disposable targets.
Unknown and blocked observations are not passes. Do not modify production.
```

```sh
agentmarshal open --contract-file /tmp/wovault-task.md
agentmarshal brief --task CR-001   # use the ID actually returned by open
```

Commit the contract separately before implementation. Do not widen scope after the
fact merely to pass the gate. After implementation, an independent reviewer checks
a specific SHA; CI attestation and `agentmarshal gate` then check that same SHA.
Do not set `AGENTMARSHAL_PIPELINE_OK_SHA` before checks actually run. Do not present
self-review as independent or record operator acceptance on the user's behalf.

The initial task `CR-001` is open for G0-00 (only group 1 of the active change).
It is not completed; fixtures/lab and actual evidence remain to be produced.
Commit the initial setup and contract before the first implementation commit.
Open separate contracts for the remaining G0 groups when their work starts.

Local validation and GitHub checks are described in [GitHub governance](github-governance.md).
Protection requires specification validation, the CI scope/journal gate and a
separate full-gate status backed by actual independent review. An independent reviewer
can inspect the candidate directly; `agentmarshal submit-review` records that
actual review. Automated reviewers may use the standard CLI adapter interface,
but no particular adapter is a contribution prerequisite.

The main repository holds only material safe for public reading. Do not run
`outbox send` without a separate instruction to publish.

## Setup verification

`scripts/check` validates journal integrity, OpenSpec in strict mode, illustrative
manifest syntax and diff whitespace. It is not a backup/restore test or security
audit. Lab experiments and AC-01–35 still need to run. A full governed loop requires
an actual candidate commit, independent review and confirmed checks.
