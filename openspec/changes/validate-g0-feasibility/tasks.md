# Tasks

No experiments have been completed. Inputs and dependency graph are in
`docs/implementation-plan.md`; the template is `docs/research/experiment-template.md`.
Each item produces a report safe for publication and the stated verification.

## 1. G0-00 — reproducible lab

- [ ] 1.1 Record authorized disposable targets, resource budget, topology and cleanup; verify that the executable allowlist contains no production targets.
- [ ] 1.2 Create a synthetic WordPress/WooCommerce/writer/drift fixture generator and pin versions; repeat generation and compare expected manifests/digests.
- [ ] 1.3 Define an evidence JSON schema with requirement/AC mapping, expected/actual/verdict and measurements; test a valid report and rejection of reports missing mandatory evidence.
- [ ] 1.4 Test runtime isolation, baseline reset and canary redaction; retain the AC-26/33 report and actual cleanup result.

## 2. G0-01 — existing-product comparison

- [ ] 2.1 Test Reaver against AC-01/03/15/17/18/31; retain the exact version, primary license/API sources, steps and actual results or blocked/unknown with a reason.
- [ ] 2.2 Repeat the same suite for Backrest using identical fixtures; retain a report identifying differences in required WordOps orchestration.
- [ ] 2.3 Repeat the suite for Duplicati and check its available API/restore/storage contract; retain a report and dependency footprint.
- [ ] 2.4 Summarize adopt/integrate/build without dropping unknowns; verify that every hard blocker has evidence and adaptation cost is separate from vendor claims.

## 3. G0-02 — WordOps inventory and access

- [ ] 3.1 Pin the OS/WordOps/PHP/database/client versions actually tested and capture a CLI/config fixture; verify REG-03/AC-03 without executing wp-config.php.
- [ ] 3.2 Test root/password, key+passphrase and sudo onboarding with host-key mismatch; retain AC-01/02 and verify no writes before bootstrap approval.
- [ ] 3.3 Test the backup key on three permitted sites and one forbidden site, plus shell/restore/path/symlink bypasses; retain AC-04/33 and a privilege diagram.
- [ ] 3.4 Publish a preliminary capability matrix with unsupported/dynamic-config cases; match every supported cell to a specific run.

## 4. G0-03 — consistency and emergency release

- [ ] 4.1 Test online capture during uploads/DDL/nontransactional changes; retain AC-09 with honest consistency/coverage outcomes.
- [ ] 4.2 Test freezing all known writers and blocking strict mode for an unknown writer; retain AC-10 with measured pause and original writer states.
- [ ] 4.3 Inject kill/partition/reboot/cancel and a stale worker after lease takeover; verify watchdog/fencing, release or needs_operator, and retain AC-10/24/35.

## 5. G0-04 — storage publication

- [ ] 5.1 Exercise Restic S3 capture/upload/commit/reconcile, concurrent prune and quota faults; retain AC-07/08/13 showing no false-complete and preservation of previous points.
- [ ] 5.2 Exercise Restic+rclone FTP interruption, delayed listings, missing rename, truncation and locking; retain AC-11/12 with actual readback.
- [ ] 5.3 Repeat corruption/recovery scenarios for standalone encrypted bundles using standard cryptography and for Duplicati reuse; test forged/replayed manifests and binding parts to point/site.
- [ ] 5.4 Test FTPS certificate/hostname/expiry/data-channel/passive-mode behavior and prohibition of silent downgrade; retain a negative-test report separately from explicit legacy FTP.
- [ ] 5.5 Summarize storage/egress cost, peak staging, readback and RTO for one fixture; verify identical inputs and document each path's limitations.

## 6. G0-05 — keys and a new control plane

- [ ] 6.1 Remove access to the original control plane/database and source in the lab, then rebuild the catalog from storage+offline kit; verify AC-31, orphan/incomplete exclusion and disabled schedules.
- [ ] 6.2 Test key rotation and old/new point reads on a new control plane; retain AC-32 and missing/wrong-key scenarios without plaintext leaks.

## 7. G0-06 — clean/create/clone/replace

- [ ] 7.1 Test clean restoration without source or plugin-download endpoints, and separately the package/cache bootstrap path; retain AC-05/15/16/20 and precise offline prerequisites.
- [ ] 7.2 Create/clone a site on an existing target with two neighbors; verify neighbors' hashes, configs, databases and continuous HTTP/write probes, AC-17/21–23.
- [ ] 7.3 Test replacement with checkpoints and failures at dump/prepare/import/config/cutover; retain AC-18/24 and proof of rollback/needs_operator without harming neighbors.
- [ ] 7.4 Test stale approval, target mutation, later orders and cancellation after writes reopen; retain AC-19/25/35 showing no blind repeated cutover/rollback.

## 8. G0-07 — isolation and security evidence

- [ ] 8.1 Test traversal/symlink/bomb/SQL fixtures and privileged-helper boundaries; retain AC-30/33 demonstrating no execution of site contents as root.
- [ ] 8.2 Introduce safe uploads/MU/admin/baseline indicators, unsupported checks and suspicious restoration; retain AC-27–29 with separate assurance states.
- [ ] 8.3 Test runtime egress and synthetic SMTP/payment/cron/webhook calls after restoration; retain AC-26 and the negative HTTP assertion AC-22.

## 9. G0-08 — decision and next backlog

- [ ] 9.1 Consolidate G0-01–07 reports and repeat end-to-end restoration using the selected storage path; verify traceability of every hard blocker and absence of critical unknowns.
- [ ] 9.2 Prepare an adopt/integrate/build/no-go ADR and obtain the owner's decision; verify that mandatory P0 is not silently reduced and limitations are published.
- [ ] 9.3 Update the roadmap/compatibility matrix and draft scoped contracts for the next stage based on the accepted path; run strict OpenSpec validation and independent evidence review.

## Workflow follow-up

- Archive the change through OpenSpec after tasks are completed and the decision is accepted.
- Verify the resulting specification and preserve links to evidence and the selected ADR.
