# Alternatives research and product direction

Research snapshot: **2026-11-04**. Conducted before the PRD and implementation.
Goal: determine whether an open external WordOps control plane already provides
backup, backup verification and stack recovery onto clean or existing VPS targets.

## Conclusion

Similar products exist. Reaver Backup is particularly close: an external dashboard,
site discovery, server agents, snapshots and restoration. Another generic backup UI
without WordOps specialization would not be justified.

The reviewed primary sources did not confirm **the complete combination** of a
public open-source project, existing WordOps fleet import, pull access, FTP/S3,
inventory/planning, clean-VPS provisioning, safe replacement on an occupied VPS
and evidence-backed restore verification. This is the result of a limited search,
not proof that no such product exists on the market.

Recommendation: build WordOps recovery orchestration on existing backup engines.
The value lies in the WordOps adapter, consistency, target planning and safe cutover.
Do not reimplement deduplication, cryptography or general-purpose storage.

## Method

Reviewed official READMEs, CLI documentation, restore guides and changelogs.
Reaver's official pages were read through direct HTTPS requests: the web tool could
not open them, but the site returned HTTP 200. Reddit/directories were used only
to discover names, not as evidence for technical conclusions.

Separate GitHub repository searches covered `wovault`, `wordops backup` and
`wordops dashboard`. The WOVault name search returned no repositories at the time;
domain, organization, package-name and trademark availability were not checked.
GitHub search is not an exhaustive search of all files or closed-source products.

“Unconfirmed” below means the reviewed sources did not describe the capability.
It does not mean the product cannot do it; a demo or separate test is needed.
Products were not installed, and performance/security were not certified.

## Comparison

| Solution | Documented capabilities | Gap relative to WOVault | Assessment |
|---|---|---|---|
| [WordOps + dashboard](https://github.com/WordOps/wordops-dashboard) | WordOps CLI manages sites/stack; dashboard provides backend tools/status | External recovery-point catalog and disaster-recovery wizard unconfirmed in reviewed descriptions | Use WordOps as the managed platform |
| [WordOps-Backup](https://github.com/mayur-chavhan/WordOps-Backup) | Full/DB/incremental, restore, cron, retention, notifications, CLI/menu | External web control plane and clean-VPS preparation unconfirmed | Study WordOps backup/restore requirements; do not claim it lacks restoration |
| [wordops-auto-backup-websites](https://github.com/reklamverme/wordops-auto-backup-websites) | Python script backing up files/MySQL to S3 | Manual site configuration; no described external inventory/restore UI | Demonstrates the need, but does not replace a control plane |
| [Reaver Backup](https://reaverbackup.com/) | Self-hosted dashboard, discovery, agents, schedules, incremental backups, offsite S3/B2/SSH, restore | Official new-server guide requires a prepared web/database stack; fully open licensing and WordOps provisioning unconfirmed | Closest direct alternative; mandatory G0 comparison |
| [Backrest](https://github.com/garethgeorge/backrest) | Open-source Restic web UI, repository operations, schedules, browse/restore | No confirmed ready-made WordOps inventory/bootstrap/cutover workflow | Strong option for manual operations; integration candidate |
| [Duplicati](https://duplicati.com/) | Backup UI, encryption, schedules, FTP/S3 backends, central-management offering | WordOps-aware database/file consistency and stack recovery unconfirmed | Real generic-backup alternative; evaluate reuse before a custom FTP engine |
| [Kopia](https://kopia.io/docs/features/) | Encryption, deduplication, policies, GUI, validity checks, optional server/API | No confirmed WordOps restore planner | Alternative engine, not a complete ready-made solution for this scope |
| [borgmatic](https://torsion.org/borgmatic/) | Config-driven Borg orchestration, DB hooks, checks, retention, monitoring | Primarily CLI/config; no described WordOps inventory/target installer | Useful reference for backup policy and database handling |
| [MainWP 6.4](https://mainwp.com/mainwp-6-4-native-backups-ai-ready-extensions-and-tighter-security/) | New built-in backup beta: full/DB/files/incremental, storage, restore, health | Requires MainWP Child on WordPress; bare-VPS WordOps bootstrap unconfirmed | Strong WordPress alternative; the older “extensions only” description is outdated |
| [ManageWP](https://managewp.com/features/backup/) | SaaS dashboard, offsite incremental backups, schedules, restore, cloning | Self-hosted WordOps control plane and OS provisioning unconfirmed | Alternative for users prioritizing a ready-made service |
| [Duplicator](https://duplicator.com/) | WordPress backup/migration packages and installer workflows | Server-side WordOps installation and fleet registry unconfirmed | Consider portability and emergency standalone installers |
| [RunCloud](https://runcloud.io/docs/restoring-runcloud-backups) | Backup UI; restore to current, other or new app/database; external storage | Own platform; importing existing WordOps without changing management unconfirmed | Close UX reference with a different operational contract |
| [Ploi](https://ploi.io/documentation/database/how-do-i-set-up-database-and-file-backups) | File/database schedules, S3/FTP/SFTP and other destinations, central UI | Panel-restore restrictions for FTP/SFTP and files; WordOps import unconfirmed | FTP backup support does not prove complete web-based restoration |

## Significant observations

### Reaver: closest, but not a complete WordOps recovery replacement

The official site describes an external dashboard, separate server agents and
user-managed storage. This already implements much of the “backup center outside
WordPress” idea. The product offers a limited free edition and paid editions;
self-hosting alone does not mean open source. Prices are not recorded because they
are unnecessary for this product decision. [Source](https://reaverbackup.com/).

The new-server restoration guide explicitly leaves web-server, database, vhost,
certificate and DNS setup to the operator. This is the gap WOVault's WordOps adapter
should address while keeping DNS under deliberate operator control. This distinction
comes from documentation, not a trial installation.
[New-server guide](https://reaverbackup.com/guides/restore-wordpress-to-new-server).

### MainWP: account for the November 2026 update

Dashboard 6.4, described on November 3, includes beta built-in backups working with
Child 6.4. The research therefore does not rely on the old claim that MainWP only
integrates backup plugins. The new feature still operates at a different layer:
WordPress sites rather than WordOps VPS provisioning.
[Release note](https://mainwp.com/mainwp-6-4-native-backups-ai-ready-extensions-and-tighter-security/).

### Server panels: useful UX, different stack ownership

RunCloud documents restoration to existing or new applications/databases. This
does not confirm safe enrollment of an existing WordOps installation. Ploi separately
states that panel-based file restoration is unavailable and database restoration
has FTP/SFTP restrictions. These differences need scenario-by-scenario validation.
[RunCloud](https://runcloud.io/docs/restoring-runcloud-backups),
[Ploi](https://ploi.io/documentation/database/how-do-i-set-up-database-and-file-backups).

### Archive verification is separate from site verification

Restic distinguishes structural checks from reading pack contents. Even successful
file verification does not prove SQL dump/runtime compatibility, uploads/database
consistency or absence of malicious code. The PRD keeps these states independent.
[Restic check](https://restic.readthedocs.io/en/stable/045_working_with_repos.html).

## Build / integrate / adopt

| Option | Benefit | Cost and condition |
|---|---|---|
| Adopt Reaver | Short path to a ready-made backup UI and fleet registry | Verify licensing, terms and WordOps coverage; add provisioning |
| Backrest + ops scripts | Mature existing Restic orchestration | Inventory/restore UX remains custom; a fork brings GPL and upstream maintenance obligations |
| Duplicati + WordOps adapter | FTP/S3 and UI already exist | Verify documented API, jobs/recovery contract and embedding suitability |
| Custom control plane + Restic | Full control of WordOps recovery and privilege model | Build UI/jobs/adapters and solve FTP separately; recommended if spikes pass |
| Custom backup/crypto engine | No engine dependency | Not justified for this project; rejected |

The product recommendation is an independent WordOps control plane, **not immediate
implementation of the entire application**. G0 tests whether extending Backrest/
Duplicati or integrating the closest alternative can meet the requirements. If an
existing solution meets P0 without a paid dependency or risky fork, favor integration.

## Experiments required before development

1. Which WordOps versions can actually be inventoried reliably through CLI/configs.
2. Restoring one site without changing neighbors on an occupied WordOps server.
3. Managing write windows: web, WP-Cron, queues, imports and external writers.
4. Restic S3 and FTP through rclone: locking, partial transfer, readback, quota and
   failure consequences. Backend availability does not replace safe-semantics testing.
5. Standalone encrypted FTP bundles as a fallback; storage cost and RTO.
6. Reaver/Backrest/Duplicati demos against S1–S6 and current license/API terms.
7. Catalog recovery from storage without the original control database or source VPS.

Research limitations: no hands-on trials, vendor interviews, performance tests,
legal name clearance or quantitative demand assessment. These do not prevent
specification, but do prevent claims of uniqueness or an automatic recommendation
to start full development immediately.
