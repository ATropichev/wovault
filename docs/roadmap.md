# Delivery and acceptance plan

Date: 2026-11-04 · Status: backlog and gates, not a calendar commitment.
P0 means the first stable release; intermediate alphas do not fulfill the entire PRD.
Team size, budget and measured throughput are unknown, so no deadlines are invented.

## G0 — Solution validation and technical spikes

For G0-00–08 ordering, dependencies, task review and decision criteria, see the
[detailed plan](implementation-plan.md). Active OpenSpec change:
[validate-g0-feasibility](../openspec/changes/validate-g0-feasibility/proposal.md).
A plan and configured tooling do not mean G0 has passed.

| Work | Output | Exit condition |
|---|---|---|
| Reaver/Backrest/Duplicati demos | S1–S6 scenarios, verified license/API limitations | Evidence explains why integration would not meet P0 more simply |
| WordOps lab | Pinned OS/release/CLI outputs and capability profiles | Inventory without PHP eval and full create/restore on a test VPS |
| Existing-server restore | Staging/cutover/checkpoint, two neighboring sites | Replacement leaves neighbors unchanged; failed replacement restores the original site |
| DB/file consistency | Writer map, online and quiesced profiles | Freeze/release verified under failure; unknown writers block strict mode |
| Storage comparison | Restic S3; rclone FTP; independent bundles; Duplicati reuse | Verified failure semantics, recovery without control DB, measured cost |
| Key recovery | Offline kit, reimport, rotation | Old and new points are readable on a new control plane |
| Security review sketch | Helper protocol and privilege diagram | Backup key cannot write/restore; no site execution as root |

G0 may end in a decision to integrate an existing product. Restic failing FTP tests
does not make FTP impossible: select and test a bundle adapter or another engine.
If neither path passes, revisit scope before implementation and explicitly record
the unmet user requirement.

## G1 — Control plane and read-only onboarding

- Public repository, dependency/license policy, CI, threat model, supported matrix.
- Auth/MFA/RBAC, server/site/storage registry, versioned inventory, host-key pinning.
- Read-only SSH protocol, bootstrap plan, restricted helper enrollment/revocation.
- PostgreSQL durable jobs, leases/retries, audit, redaction, scheduler heartbeat.

Gate: demonstrate inventory on two servers with multiple sites; no changes before
approval; failures/host-key changes block safely; no secret-canary leaks.

## G2 — S3 backup alpha

- Full capture, DB-only/files-only, online consistency and coverage reports.
- Restic adapter, manifest/commit reconciliation, catalog and existing-repository import.
- Scheduling/timezone/retention/pins, progress, notifications and freshness monitoring.
- Structural/full/subset checks and file/database restoration into an isolated lab.

Gate: interrupted jobs create no complete points; storage and control-database
recovery work. Label the alpha S3-only, without presenting it as complete P0.

## G3 — Recovery beta and FTP

- Validated FTP/FTPS adapter with readback, partial-transfer resume and recovery catalog.
- Clean-VPS provisioning and restore; existing-WordOps create/clone/replace.
- Plan hash/approval/revalidation, safety checkpoint, rollback/reconciliation.
- URL/secrets policy, isolated previews, WordOps metadata consistency, TLS/DNS states.
- Quiesced profiles for validated writer combinations.

Gate: all ACs for clean/existing targets and FTP/S3; failure injection at every step;
rollback without harming neighbors. Verify support for old points after upgrades.

## G4 — Assurance and the first stable release

- Checksum/baseline/static/database findings; quarantine, pins, investigation states.
- Scheduled isolated restore drills, HTTP assertions, blocked egress.
- Benchmark profile and published RPO/RTO measurements with conditions.
- External security review of critical helpers/parsers and release/recovery runbooks.
- RU/EN UI, accessibility, administrator guide and control-plane disaster recovery.

Gate: all P0 requirements and mandatory acceptance scenarios below are met.
No `not_checked/unsupported` result is displayed as passed. Document limitations
before release.

## G5 — After the stable release

P1: additional protected storage, validated Object Lock profile, system-level sensors,
YARA/ClamAV/feeds, other OS/architectures, more WordOps versions, remote database/media
adapters. OIDC, agency scopes and later maintenance operations are discussed separately.
Fleet-wide production upgrades must not be added implicitly to backup scope.

## Mandatory acceptance scenarios

Each scenario has a machine-readable report, input fixture, expected result,
secret-free logs and requirement-ID references. Only lab VPS instances are used.

| ID | Scenario | Expected outcome | Requirements |
|---|---|---|---|
| AC-01 | Connect by root password; separately SSH key+passphrase and sudo-login | Host key verified; inventory before writes; secret not persisted by default | REG-01/02/05, RST-01 |
| AC-02 | Wrong password, root SSH disabled, host-key mismatch | Clear error; SSH policy is not weakened; no mutation | REG-04, RST-01, NFR-02 |
| AC-03 | WordOps registry/vhost discrepancies and dynamic config detected | Coverage gap/blocker; site PHP is not executed | REG-02/03 |
| AC-04 | One backup account, three permitted sites and a fourth forbidden site | First three are backed up; fourth site/other paths/restore/shell remain inaccessible | REG-05, BKP-04, NFR-02 |
| AC-05 | Full backup; all original plugin-download/GitHub endpoints then become unavailable | Restore uses retained files | BKP-03, RST-05 |
| AC-06 | DB-only/files-only snapshot | No full-restore promise; advanced restoration needs a separate plan | BKP-01/07, RST-07 |
| AC-07 | SSH/network interruption and crash between upload/commit/database registration | No false complete; retry/reconcile without duplicates | BKP-02/07, NFR-03 |
| AC-08 | ENOSPC/inode exhaustion/quota and storage timeout | Stop without damaging older points; visible reason and notification | BKP-06, STO-01/02, UI-02 |
| AC-09 | Database/uploads/DDL/nontransactional-table changes during online backup | Honest consistency status; no strict guarantee claimed | BKP-05 |
| AC-10 | Quiesced web+cron+queue+external writer; then cleanup failure | Confirmed window; original states restored or needs_operator + alert | BKP-05/06 |
| AC-11 | FTP server lacks rename or returns delayed listings | No false commit; actual readback and safe retry | STO-02/03, BKP-07 |
| AC-12 | FTP part/manifest replaced or truncated | Integrity failed; production restoration blocked | STO-03/04, VER-01/02 |
| AC-13 | Retention after repeated backup failures; pinned incident snapshot | Last full and pinned points preserved; dependencies respected | BKP-08 |
| AC-14 | DST shift, missed runs, two workers with one idempotency key | Predictable next-run/catch-up; one committed point | BKP-02, NFR-03 |
| AC-15 | Original VPS destroyed; new compatible clean target | Approved WordOps bootstrap; full restore without the source | S3, RST-02/04/05 |
| AC-16 | Target without WordOps but with another panel/occupied services | Conflicting stack and blocker; nothing removed | RST-02/04 |
| AC-17 | WordOps target with two existing sites; create a third | New site works; neighbors' hashes/configs/databases unchanged | RST-04/05 |
| AC-18 | Replace one site; fail at dump, prepare, database import, config validation or cutover | Mandatory checkpoint; rollback/needs_operator; neighbors intact | RST-06/10 |
| AC-19 | Target/domain/inventory changed after approval | Plan stale; apply blocked until new approval | RST-03 |
| AC-20 | Incompatible PHP extensions/database collation/dump client/WordOps | No silent shared-stack upgrade; blocker and explanation | REG-02, RST-02/04 |
| AC-21 | Clone to another domain with serialized values and SMTP/payment/1C integrations | Correct URLs; test integrations disabled, egress blocked | RST-08/09, VER-03 |
| AC-22 | HTTP 200 contains fatal/error/login instead of the expected page | Smoke test fails; cutover is not considered successfully verified | RST-09 |
| AC-23 | DNS does not point to target; ACME HTTP unavailable | Preview works through override; public TLS is not declared ready | RST-09 |
| AC-24 | Worker loss/reboot after every mutating restore step | Durable reconciliation; no blind repeated cutover | RST-10, NFR-03 |
| AC-25 | WooCommerce accepted new orders after the snapshot | Loss of later data explicitly shown before replacement; no automatic merge promised | RST-07 |
| AC-26 | Test restore with scheduler, SMTP, webhooks and payments | No request leaves isolation; production unaffected | VER-03, RST-08 |
| AC-27 | Extra PHP in uploads, modified MU plugin, new administrator, baseline drift | Findings with scope/evidence/confidence; no automatic cleanup | SEC-01/02/03 |
| AC-28 | Plugin without official checksums, unavailable feed or scanner timeout | Unsupported/not_checked; no green security pass | VER-01, SEC-01 |
| AC-29 | Suspicious point followed by a production-restore attempt | Isolation by default; override only by administrator with a reason | RST-11, SEC-03 |
| AC-30 | Traversal/symlink/bomb/dangerous SQL in an archive | No out-of-scope write or root execution; job safely stopped | NFR-02, RST-11 |
| AC-31 | Control database/plane lost; storage+offline key kit available | Catalog rebuilt; restore possible; plans disabled | S6, STO-04/05 |
| AC-32 | Key rotation and WOVault upgrade | Old points readable; old approvals invalid | STO-05, NFR-04 |
| AC-33 | Leak/wrong scope through API/download/argv/log/notification | Canary secrets not visible; viewer cannot download a dump | Section 3, NFR-02/03, UI-02 |
| AC-34 | Scheduler stopped, notification channel unavailable | External heartbeat/monitor reports stale state; delivery failure visible | UI-02, NFR-03 |
| AC-35 | Cancel before/after cutover; site has already accepted new writes | Only permitted cancellation; rollback after writes needs a new plan | RST-10 |

## Comparing existing products at G0

Start with AC-01/03/15/17/18/31, the main differentiator. Then assess storage,
security scopes and licensing. Each result records the tested version, environment,
steps, actual outcome and verdict. An untested vendor claim is documented, not tested.
An unverified capability is unknown, not failed.

## Pilot metrics

Measure the share of sites with a fresh full point, age of the latest successful
restore drill, backup window, pause time, recovery to serving and public cutover,
storage/egress cost, false-positive findings and response time. The site owner sets
RPO; validate whether the schedule can meet it given queues and failures.
The initial retention policy of 14 daily / 8 weekly / 12 monthly is an editable
preset, not a commitment suitable for every store and customer.
