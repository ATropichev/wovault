# Proposal

## Why

WOVault currently exists only as a specification. Before building its control plane,
validate whether an existing product can be reused and whether safe WordOps restoration,
FTP recovery and recovery without the original control plane are feasible.

## What Changes

- Execute G0-00–08 from `docs/implementation-plan.md` in a synthetic lab.
- Introduce reproducible evidence reports with distinct planned/documented/tested
  states and requirement → AC → experiment → decision traceability.
- Compare Reaver, Backrest and Duplicati against identical hard requirements.
- Validate inventory/privileges, consistency, storage commit, key recovery,
  clean/create/replace and isolation before final architecture selection.
- Update the compatibility matrix and ADR 0001 based on evidence.

Out of scope: full application implementation, production access, paid subscriptions,
automatic DNS cutover and claims of support for untested versions. Mandatory web UI,
registry, SSH pull, S3, FTP/FTPS, verification and both restore target modes remain
requirements for the first stable release.

## Capabilities

### New Capabilities

- `feasibility-evidence`: reproducible qualification evidence for implementation
  decisions and supported combinations; this is the G0 process, not a ready backup API.

### Modified Capabilities

No accepted OpenSpec capabilities exist. The PRD's product requirements remain normative.

## Impact

Affects lab fixtures/harnesses, sanitized reports, compatibility matrix, ADRs and
backlog. The application stack, engines and storage format remain proposals until
G0-08. The lab requires separately designated disposable targets and agreed limits.
Planning this change is not evidence of completed experiments.
