# Design

## Context

Motivation is in proposal.md; product boundaries are in docs/PRD.md. No implementation
exists. The roadmap defines AC-01–35 but not execution protocols. G0-00–08 details
and observations are in docs/implementation-plan.md; this change binds them to an
evidence contract.

## Goals / Non-Goals

**Goals:** obtain repeatable results sufficient for engine/architecture decisions,
and an early end-to-end restore with failures. Evaluate neighbor preservation and
control-plane recovery alongside capture success.

**Non-Goals:** a stable application API, production deployment, a final UI framework,
custom cryptography or a supported-version range inferred from upstream lists.

## Decisions

1. **One report format, multiple implementations.** Use experiment-template.md for
   each candidate and scenario. Free-form notes make comparison harder and hide
   unknowns. In G0-00, prepare machine-readable results with per-scenario verdicts;
   their storage format does not substitute for an actual run.
2. **Start with a small reproducible fixture.** This supports interruption at every
   step without the cost of a full-size benchmark. Use the large profile separately
   for staging and RTO estimates, not to prove correctness under every failure.
3. **Separate lab roles.** Source, clean/existing targets and control/storage have
   explicit roles. Block restore-runtime egress; provisioning downloads happen in
   a separate phase without opening the restored site's network access.
4. **G0-01/02/04 are independent after G0-00; decide after restoration.** A successful
   engine benchmark does not complete G0 without catalog/key recovery and replacement
   fault injection.
5. **The engine remains an experimental variable.** Compare Restic S3, rclone FTP,
   independent encrypted bundles and Duplicati reuse. Choosing bundles requires
   separate proof of authenticated publication; no new cryptography is created.
6. **Evidence is not approval.** OpenSpec validates structure; AgentMarshal briefs
   deliver contracts, and reviewers examine actual outputs and SHAs. An extension
   manifest neither runs experiments nor records the project owner's decision.

## Risks / Trade-offs

- [Lab differs from real VPS environments] → publish a narrow tested matrix and
  unsupported cases; expand support through separate runs.
- [Unknowns become an argument for custom development] → require evidence for hard
  blockers; record unavailable trials as blocked.
- [Freeze requires write capability] → use a separate restricted protocol, target-side
  watchdog/fencing and explicit cleanup tests, without expanding the regular backup key.
- [Offline bootstrap costs more than file backup] → test cache/mirror and dependency
  redistribution rights; describe installation-artifact availability boundaries.
- [Rollback loses new writes] → test the write-reopening boundary and a new plan
  after it; do not promise automatic rollback from every state.

## Migration Plan

There is no production migration. Each lab run starts from a known baseline and
ends with a cleanup report; a lost baseline requires reset, not blind retry.
After G0-08, update the ADR/compatibility matrix and open separate G1 changes or
integration changes for the selected product. Archive this change only after evidence
and an accepted decision; retain failed hypotheses as results rather than deleting them.
