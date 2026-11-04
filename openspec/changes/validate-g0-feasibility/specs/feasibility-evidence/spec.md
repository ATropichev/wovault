# Spec Delta

## Purpose

Give the project owner reproducible grounds for adopt/integrate/build decisions
and supported combinations, while distinguishing requirements, claims and test results.

## ADDED Requirements

### Requirement: Reproducible experiment evidence

Every G0 report SHALL connect requirement/AC IDs, versions, fixture digest,
reproducible steps, expected/actual and evidence to one of these states: planned,
documented, tested-pass, tested-fail, blocked, unknown.

#### Scenario: Vendor claim without a run

- **WHEN** upstream describes a capability but its scenario has not been run
- **THEN** the report records documented and a primary source, not tested-pass

#### Scenario: Repeated experiment

- **WHEN** another operator repeats an experiment using its report
- **THEN** exact inputs and procedures are available, and the new run retains its own actual/verdict

### Requirement: Authorized isolated experiments

G0 execution SHALL use only explicitly authorized disposable lab targets and
synthetic fixtures. Public evidence SHALL contain no credentials, customer data
or raw private inventories. Basis: NFR-02, AC-26/33.

#### Scenario: No designated lab

- **WHEN** authorized targets or resource limits are undefined
- **THEN** execution is marked blocked and no production endpoint is used by default

#### Scenario: Secret canary in output

- **WHEN** a canary appears in a scenario's report, argv or logs
- **THEN** AC-33 receives tested-fail and the material is excluded from the public report

### Requirement: Comparable reuse decisions

The G0 decision SHALL compare candidates against the same hard requirements S1–S6
and AC-01/03/15/17/18/31, including API/license constraints, adaptation and maintenance.
Unavailable checks SHALL retain blocked/unknown instead of denying a capability.

#### Scenario: Candidate unavailable

- **WHEN** a candidate's trial or source is unavailable for the required test
- **THEN** the report describes the limitation and does not claim tested-fail for that scenario

### Requirement: Qualify storage and recovery together

Engine/format selection SHALL rely on fault injection and restoration from both
mandatory storage profiles, including source/control-database loss and key rotation.
Successful upload alone SHALL NOT satisfy STO-01–05, AC-07/11/12/31/32.

#### Scenario: Interrupted or forged publication

- **WHEN** a part is missing or truncated, a manifest is forged, or a worker is lost before commit
- **THEN** the report checks rejection of false-complete, preservation of previous points and safe retry

#### Scenario: Center loss

- **WHEN** only storage and separately retained recovery material are available
- **THEN** catalog rebuild, old/new point readability and disabled schedules are verified

### Requirement: Qualify safe WordOps replacement

G0 SHALL validate clean/create/replace on a pinned matrix, with checkpoints,
step-level failures and probes of two neighboring sites. Requirements: REG-03,
BKP-05/06, RST-03/06/10, AC-03/10/15/17–20/24/35.

#### Scenario: Worker loss during freeze or cutover

- **WHEN** a worker is lost or its lease becomes stale after a mutating step
- **THEN** the report verifies fencing/reconciliation, original writer states and no harm to neighbors

#### Scenario: Writes accepted after cutover

- **WHEN** the restored site has already accepted new writes
- **THEN** automatic rollback is not declared safe; a new plan with explicit loss of later data is verified

### Requirement: Keep assurance outcomes independent

G0 reports SHALL separately show transfer, completeness, consistency, integrity,
restore tests and security findings, with coverage and time. Unknown/unsupported
SHALL NOT become passed. Basis: VER-01–03, SEC-01–03, AC-22/26–30.

#### Scenario: Successful upload with unchecked runtime

- **WHEN** upload completes but the isolated runtime has not been tested
- **THEN** restore-test status remains not_checked regardless of transfer success

### Requirement: Evidence-bound gate decision

G0-08 SHALL explicitly choose adopt/integrate/build or no-go and bind the decision
to G0-01–07 evidence. An unknown critical outcome SHALL block final selection;
mandatory scope is not reduced without a separate project-owner decision.

#### Scenario: FTP path fails qualification

- **WHEN** tested FTP options fail corruption/recovery checks
- **THEN** G0 records no-go or an explicit scope revision, not S3-only as complete P0

#### Scenario: Planning artifacts exist

- **WHEN** proposal/specs/design/tasks validate successfully but experiments have not run
- **THEN** G0 remains open, tasks stay unchecked and the ADR remains proposed
