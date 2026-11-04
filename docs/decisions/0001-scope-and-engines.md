# ADR 0001: WordOps recovery control plane and backup-engine reuse

Date: 2026-11-04 · Status: proposed; requires G0 spikes.

## Context

Ready-made web backup products exist. The research does not justify a new generic
backup engine. The project must enroll an existing WordOps fleet and restore sites
and their environments to clean/existing VPS targets through a validated plan.
In addition to S3, ordinary FTP storage is required, despite lacking some S3 properties.

## Decision

1. Build an independent control plane for WordOps inventory, policies, jobs, assurance
   and recovery. Do not make a WordPress plugin the central component.
2. Host the control plane separately and use SSH pull. No storage keys on the source.
3. Propose a Restic subprocess adapter for S3. Do not copy Backrest's UI/code.
4. Support FTP/FTPS through a validated backend or independent encrypted bundles.
   This is not a final engine choice before G0. The default design path is full
   bundles with the standard age implementation; no custom cryptography.
5. Separate backup and restore principals. Routine backups do not require persistent
   root access; root/sudo is allowed for bootstrap and approved restoration.
6. Start with single-organization deployment and a limited compatibility matrix.
7. Publish original code/documentation under MIT. Check licenses and notices for
   external binaries, libraries and bundled components at the selected versions.

## Alternatives

- **Adopt Reaver.** The closest ready-made product, but WordOps provisioning and an
  open-source licensing model for the entire project are unconfirmed. Requires a G0 demo.
- **Backrest fork.** A quick generic UI foundation, but WordOps workflows still need
  custom work, with upstream and GPL-3.0 obligations. No fork is chosen without validation.
- **Duplicati reuse.** A strong storage/UI candidate; check its API, recovery orchestration
  and dependency footprint before a final rejection.
- **Restic + rclone for everything.** Possible, but FTP transport alone does not prove
  the required locking/commit/recovery semantics. Test before claiming reliability.
- **Custom dedup/crypto engine.** Rejected: its risk and cost do not serve the goal.

## Consequences

A custom UI/jobs layer remains substantial work. Two storage paths increase testing;
full FTP bundles use more space/bandwidth. In return, the format should not depend
on a long incremental chain on a weak backend. S3 deduplication and standalone FTP
points share a product-level recovery contract, but not a cost or speed guarantee.

The system does not claim immutable backups in P0 merely because access uses pull.
Protection against compromise of the control plane itself requires an additional
independent protected copy. Public GitHub content contains no real credentials/data.

## Reconsideration condition

If G0 shows that extending an existing open product meets P0 with less risk, choose
integration and update the ADR/PRD. If FTP bundles fail recovery or corruption tests,
do not ship a stable product with unvalidated FTP support.
