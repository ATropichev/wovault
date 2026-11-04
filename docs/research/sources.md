# Sources and research log

Checked: 2026-11-04. These primary sources were actually opened during preparation.
Statements in the PRD, architecture and ADR beyond these facts are design decisions.
These documents do not reproduce third-party articles, code or illustrations.

| ID | Source | What was checked |
|---|---|---|
| W01 | [WordOps repository](https://github.com/WordOps/WordOps) | CLI, upstream platform claims and managed components |
| W02 | [WordOps site commands](https://docs.wordops.net/commands/site/) | create/list/info/update and site operations |
| W03 | [WordOps installation](https://docs.wordops.net/getting-started/installation-guide/) | Installation methods and environment dependencies |
| W04 | [WordOps dashboard](https://github.com/WordOps/wordops-dashboard) | Built-in dashboard description |
| W05 | [WordOps stack](https://docs.wordops.net/commands/stack/) | Shared components and upgrade/migrate operations |
| C01 | [WordOps-Backup](https://github.com/mayur-chavhan/WordOps-Backup) | Full/incremental/DB, restore, CLI/menu, schedules |
| C02 | [wordops-auto-backup-websites](https://github.com/reklamverme/wordops-auto-backup-websites) | File/database-to-S3 script and manual site list |
| C03 | [Reaver home](https://reaverbackup.com/) | Dashboard/agents/discovery/offsite and edition model |
| C04 | [Reaver new-server restore](https://reaverbackup.com/guides/restore-wordpress-to-new-server) | Target-server components that remain the operator's responsibility |
| C05 | [Backrest](https://github.com/garethgeorge/backrest) | Restic web orchestration, repository operations, GPL-3.0 |
| C06 | [Duplicati home](https://duplicati.com/) | Backup platform and central-management offering |
| C07 | [Duplicati source](https://github.com/duplicati/duplicati) | Public project; exact dependency terms will be checked for the selected version |
| C08 | [Duplicati FTP](https://docs.duplicati.com/backup-destinations/standard-based-destinations/ftp-destination) | FTP backend, upload verification and transport options |
| C09 | [Kopia features](https://kopia.io/docs/features/) | Encryption, GUI, checks, server/API |
| C10 | [borgmatic](https://torsion.org/borgmatic/) | Database backup, consistency, monitoring, configuration-driven approach |
| C11 | [MainWP 6.4 release](https://mainwp.com/mainwp-6-4-native-backups-ai-ready-extensions-and-tighter-security/) | New backup beta, published 2026-11-03 |
| C12 | [MainWP Child 6.4](https://voice.mainwp.com/changelog/mainwp-child-64) | Child plugin support for the new mechanism, dated 2026-11-02 |
| C13 | [ManageWP backup](https://managewp.com/features/backup/) | Managed offsite, schedules, restore, cloning |
| C14 | [Duplicator](https://duplicator.com/) | WordPress backup/migration product positioning |
| C15 | [RunCloud restore](https://runcloud.io/docs/restoring-runcloud-backups) | Current/other/new app+DB restore |
| C16 | [RunCloud create backups](https://runcloud.io/docs/creating-backups) | Storage/schedules; external-storage behavior |
| C17 | [Ploi backup documentation](https://ploi.io/documentation/database/how-do-i-set-up-database-and-file-backups) | Destinations and panel-restore restrictions |
| E01 | [Restic repositories](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html) | S3/rclone backends, encryption/repository access |
| E02 | [Restic checks](https://restic.readthedocs.io/en/stable/045_working_with_repos.html) | Structural check versus full/subset data reads |
| E03 | [Restic retention](https://restic.readthedocs.io/en/stable/060_forget.html) | forget/prune and append-only considerations |
| E04 | [rclone FTP](https://rclone.org/ftp/) | FTP/FTPS transport requiring capability testing |
| E05 | [age](https://github.com/FiloSottile/age) | Existing encryption implementation for the bundle option |
| E06 | [AWS Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) | WORM, object versions, retention and delete markers |
| V01 | [mariadb-dump](https://mariadb.com/docs/server/clients-and-utilities/backup-restore-and-import-clients/mariadb-dump) | Snapshot limitations and dump/import compatibility |
| V02 | [WP-CLI core checksums](https://developer.wordpress.org/cli/commands/core/verify-checksums/) | Official core-verification mechanism |
| V03 | [WP-CLI plugin checksums](https://developer.wordpress.org/cli/commands/plugin/verify-checksums/) | Official plugin-verification mechanism |

## Search queries

- `"WOVault"`, GitHub repository search `wovault`.
- `WordOps backup restore web interface self hosted backup multiple servers`.
- `"WordOps" "backup" github`, GitHub repository search `wordops backup`.
- `"WordOps" "dashboard" github backup restore`, GitHub search `wordops dashboard`.
- `Reaver Backup WordOps restore self hosted` and refinements for the official domain.
- `site:mainwp.com "Built-In Backups" restore`.
- `site:runcloud.io backup restore server backup WordPress S3`.
- `site:ploi.io documentation backup restore server S3 FTP`.
- Follow-up searches for Duplicati FTP, Restic/rclone, WordOps CLI and WP-CLI checksums.

Search also found the archived `harsh8511/wordops-backup-sftp` and GDrive scripts.
They were not assessed as full alternatives to a UI product. Third-party reviews,
Reddit and directories were not used to substantiate capabilities or security.

## Reliability and reproducibility

- Public pages can change: comparisons must carry a snapshot date.
- Pin exact releases/commits and binary versions in G0 lab reports.
- Do not turn WordOps upstream support lists into WOVault promises without testing.
- MainWP research uses the new release note rather than an older knowledge base.
- Reaver was read through direct HTTPS after a web-reader failure; no login was needed.
- Search cannot establish the absence of closed, obscure or new alternatives.
- Pricing, market share and SLA estimates were not used; they were not checked separately.
- Unavailable UpdraftPlus/WP Umbrella pages were excluded from the evidence matrix.
