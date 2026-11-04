# WOVault — Product Requirements Document

Version: 0.1 · Date: 2026-11-04 · Status: ready for discussion and implementation.

These are requirements for a future product. A working application, installer and
validated compatibility matrix do not yet exist. Decisions marked as proposals
require technical validation before adoption. Research preceded the requirements:
[alternatives](research/landscape.md), [sources](research/sources.md).

## 1. Product and problem

WOVault is an independent external backup and recovery control plane for WordOps
sites, with a web UI. It maintains server records, pulls data over SSH, verifies
backups and helps restore a site after the original VPS is lost.

The target user is an administrator or small agency managing several WordOps VPS
instances. They need to know which sites are protected, how fresh their backups
are, whether they can be restored and which changes need investigation.

The primary outcome: an operator selects a retained recovery point and target VPS,
reviews the discovered environment and validated plan, then restores a new site or
replaces an existing one. The system preserves a rollback path for replacement
and verifies the site before public traffic is switched over.

## 2. Goals, boundaries and definitions

### Goals for the first stable release

- Centrally protect sites across multiple WordOps servers.
- Work when wp-admin is unavailable or the original VPS is completely lost.
- Support S3-compatible storage and FTP/FTPS as independent storage destinations.
- Restore any retained full recovery point within validated compatibility limits,
  without requiring access to the original server or GitHub.
- Provide verifiable integrity, consistency and restoration reports.
- Detect selected compromise indicators and anomalies without automatic remediation.
- Publish source code and documentation on GitHub without a mandatory paid service.

### Outside the first release

Full disk/OS images; mail-server management; continuous replication and PITR;
automatically merging new WooCommerce orders into an older database; arbitrary
panels instead of WordOps; independent SaaS tenants; automatic DNS migration;
guaranteed detection of every intrusion; automatic fleet-wide upgrades.
WordPress Multisite, remote databases and external media/object storage are
initially detected as special configurations and prevent a full-coverage claim.

### Terms

| Term | Meaning |
|---|---|
| Server | A VPS with a pinned SSH identity and inventory history |
| Site | A distinct WordOps object with an immutable WOVault ID; its domain can change |
| Plan | Site selection, schedule, contents, storage, checks and retention |
| Recovery point | A committed set of files, database dump and metadata; not merely a job run |
| Full recovery point | Contains everything needed to restore a site; its physical storage may use deduplication |
| DB-only / files-only | A partial backup, not a standalone full recovery point |
| Inventory | Observations about a server, with time, source and trust level |
| Recovery kit | An export of catalog information, keys/instructions and configuration for recovery without the old control plane |
| Consistent snapshot | Data captured while all agreed write sources are confirmed to be stopped |

“From any backup” means any available full recovery point that passes the required
checks. A point deleted by retention, damaged or partial must not be presented
as ready for full restoration.

## 3. Users and access

| Role | Permissions |
|---|---|
| Administrator | Servers, keys, bootstrap, storage, policies, restoration and backup deletion |
| Operator | Run authorized backups/checks; prepare restoration; apply it within the permitted scope |
| Viewer | Status, sanitized reports and history; no secrets, dumps or restoration |

Permissions apply to servers/sites and operations. Reading a report does not grant
permission to download a database. Viewing a masked secret does not reveal its
original value. An administrator can prohibit an operator from replacing production
sites. Restoration permission does not imply permission to delete backups.

## 4. Scenarios

### S1. Connect an existing WordOps server

The operator supplies a name, address, port, SSH username and password or key with
passphrase. Root or a user with sufficient sudo privileges is allowed for bootstrap.
The SSH fingerprint is verified through a trusted channel before credentials are
sent. Read-only inventory reports the OS, versions, services, sites and unusual
configurations.

After a separate bootstrap plan is approved, a restricted helper is installed and
a backup user is created or enrolled. The root password is not retained by default.
The user selects sites and assigns a plan. Newly discovered sites appear as
unprotected; automatic enrollment requires an explicitly enabled policy.

### S2. Daily backup and monitoring

A plan pulls files and databases from each selected site. One unavailable site
does not cancel backups of the others. The operator sees the latest successful
full recovery point, database/file age, storage-check result and last restore-test
date. Missing successful backups trigger an alert even if the scheduler did not run.

### S3. Lost VPS: restore onto a clean target

The operator selects a recovery point and adds a new VPS. Inventory confirms a
supported OS and no conflicting stack. The wizard proposes installing a validated
WordOps version, required components and site, then restoring the data. Before
application it shows changes, space requirements, dependencies, warnings and steps
that have no automatic rollback. DNS remains a separate operator action.

### S4. Restore onto an existing WordOps server

The wizard shows existing sites. It can create a missing site, clone to another
domain or replace a selected existing site. Replacement requires separate approval,
paused writes, preservation of the current state and verification that the original
site/plan has not changed since review. Other sites remain unaffected. Shared
services and their major versions are not automatically replaced.

### S5. Suspected compromise

The system flags unexpected code changes, new administrators or executable files
in uploads. The suspicious backup is retained and labeled, and a trusted older
point is pinned. Analysis takes place separately from production. By default,
such a backup may only be restored into isolation for investigation.

### S6. Lost control plane

WOVault is installed on a new external server. The administrator imports a recovery
kit or connects storage and separately retained keys, then rebuilds the catalog
from manifests. Neither the old control database nor a working source site is
required. Plans remain disabled until access and server identities are reverified.

## 5. Server registry and inventory

**REG-01 (P0).** The registry includes UUID, name, address, SSH port, host key,
tags/environment, permitted sites, credential references, capability profile,
latest inventory, last contact time, bootstrap state and adapter compatibility.

**REG-02 (P0).** Discover OS/architecture, WordOps, Nginx, PHP-FPM and extensions,
MariaDB/MySQL and client versions, WP-CLI, disks/inodes, mounts, ACLs/owners,
enabled vhosts, domains/aliases, docroots, cache settings, site-to-database mapping,
prefix, external media and symlinks. Separately collect site cron, systemd timers
and required include configs within the granted access. Show inaccessible sections.

**REG-03 (P0).** Use a WordOps adapter that verifies actual syntax and versions;
do not assume the CLI has a JSON API. Reconcile the WordOps catalog with active
vhosts and the filesystem. Discrepancies require a decision, not a hidden repair.
Inventory must not execute site PHP, including `wp-config.php`. Dynamic configs
and external secrets need an explicit adapter; missing information is a visible blocker.

**REG-04 (P0).** Support rescanning and diffs. Host-key changes block jobs until
reverification. Sites that disappear from a server retain their history and backups;
removing a server in the UI does not automatically delete them. Re-registration
must not create duplicates or lose links to previous recovery points.

**REG-05 (P0).** Show account capabilities: read files, dump DB, collect configs,
bootstrap and restore. An existing deploy login is allowed with suitable privileges,
but a separate read-only account is recommended. A backup user may have an explicit
allowlist of several sites; this scope is displayed in the UI.

## 6. Backup plans

**BKP-01 (P0).** A plan selects specific sites or a selection rule with a preview,
full/DB-only/files-only mode, includes/excludes, storage, schedule, timezone,
retention, resource limits, consistency policy and checks.

**BKP-02 (P0).** Scheduling supports intervals, daily/weekly times and advanced cron;
the UI shows the next five runs. Store UTC and an IANA timezone, handling DST correctly.
Missed runs are coalesced into one catch-up according to policy. Retries are bounded,
with backoff and an idempotency key. Losing a worker response must not cause the same
run to create two completed recovery points.

**BKP-03 (P0).** A full recovery point includes all site files, the database, hidden
files, plugins, themes, MU plugins, vendor/runtime dependencies, required parent-level
config and a version/recovery manifest. Restoration must not rely on old distributions
or licensed plugin downloads remaining available. Cache/log/old-backup exclusions are
explained and visible; the entire `vendor` directory must not be excluded by default.
External dependencies are captured through an authorized adapter or reported as gaps.

**BKP-04 (P0).** Capture uses SSH pull, with no storage keys written to the protected
server. Database passwords must not appear in argv or logs. WordPress services do
not need WOVault plugins. Any source-side staging is private, quota-limited and
cleaned after confirmed transfer; the recovery kit describes coverage.

**BKP-05 (P0).** Consistency states:

| Mode | Guarantee |
|---|---|
| online | A consistent transactional dump of supported tables and files captured over an interval; no cross-resource atomicity |
| quiesced | All configured writers are stopped/blocked; files and database are captured within a confirmed window |
| degraded / unknown | Consistency could not be confirmed; the reason and limitations are explicit |

`--single-transaction` does not ensure consistency for nontransactional tables,
concurrent DDL or the database together with files. These limitations are described
in [mariadb-dump](https://mariadb.com/docs/server/clients-and-utilities/backup-restore-and-import-clients/mariadb-dump).
A plain `.maintenance` file does not prove that cron, 1C integrations, queues or
external imports have stopped. Strict mode requires a writer adapter and a timeout
that restores the previous state; it is unavailable with an unknown writer.
Pre-transferring files reduces the pause, but final reconciliation occurs inside
that window.

**BKP-06 (P0).** Apply global/per-server/per-site limits, IO/CPU/network limits,
queue deduplication and mutual exclusion between backup, restore and schema changes.
External deploy/import coordination requires integration; without it, the UI must
not promise quiesced capture. Timeout, ENOSPC and SSH interruption are not successes.

**BKP-07 (P0).** The manifest records UUIDs, capture intervals, contents, exclusions,
versions, file/dump digests, limitations, engine/format/key IDs and transfer results.
Publish a point only after verifying required objects and the final commit record.
Incomplete transfers remain separate from the catalog of ready recovery points.

**BKP-08 (P0).** Retention applies only to completed points and accounts for dependencies,
legal/incident pins and a minimum number of recoverable copies. Never automatically
delete the last full point after repeated failures. Deletion and prune have a separate
queue, permissions, preview plan and journal; protected storage may delay physical
deletion. The UI must not classify that delay as a backup failure.

## 7. Storage and keys

**STO-01 (P0).** S3-compatible settings: endpoint, region, bucket, prefix, credentials,
TLS and path-style addressing where needed. Capability testing includes list/read/write/
delete within a dedicated test prefix, multipart operations, restoration of a small
encrypted dataset and space/quota measurement where the backend reports it. IAM scope
is limited to the repository; automatic cleanup uses separate privileges where possible.

**STO-02 (P0).** FTP/FTPS settings: host, port, TLS mode, passive settings, path,
credentials, timeouts and capability testing. FTP without TLS is an explicit legacy
mode; the UI warns that credentials and connection metadata are unprotected even
when archives are encrypted. Do not describe FTP as guaranteed immutable storage.

**STO-03 (P0).** Proposal: Restic for S3; independent encrypted bundles with verifiable
manifests and uploads split into parts for FTP/FTPS. Physical FTP deduplication is not
promised for the first release. An interrupted upload does not replace an earlier
point. FTP commit verification relies on actual contents, not assumed atomic rename.
The final format requires a spike and an [ADR](decisions/0001-scope-and-engines.md).

**STO-04 (P0).** Encryption before transfer is mandatory. Keys are not stored as
plaintext in the control database and do not depend on the VPS root password.
The recovery kit is exported encrypted, with its key/password stored separately.
The UI verifies that the operator has retained recovery material. A lost decryption
key cannot be “reset” like a UI password.

**STO-05 (P0).** Connecting existing storage rebuilds the catalog from manifests
without the old control database. Secret fields and filenames must not leak through
an unencrypted catalog. Key-ID rotation must not make old points unreadable.

**STO-06 (P1).** A second destination, isolated copy and validated deletion protection.
S3 Object Lock requires its own compatibility profile, object-version tracking and
retention handling; it cannot simply be enabled over an engine's mutable lock/index
objects. WORM semantics are described in the [AWS documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html).

## 8. Verification and compromise indicators

**VER-01 (P0).** Separate fields for transfer status, archive integrity, database
consistency, restore tests and security findings. Each has scope, timestamp,
tool/rule version, evidence and `passed / failed / warning / not_checked / unsupported`.
A single exit code must not produce one green “clean and recoverable” label.

**VER-02 (P0).** Verify the manifest and mandatory objects after writing. Schedule
structural checks, subset reads and full reads within a defined cycle. Account for
egress/time budgets and show coverage explicitly. Restic `check` without `--read-data`
does not verify every pack file's contents; see the [documentation](https://restic.readthedocs.io/en/stable/045_working_with_repos.html).

**VER-03 (P0).** Restore tests include decryption, safe extraction, import into an
isolated database, table/key-record checks, compatible runtime startup, HTTP smoke
tests and site-specific assertions. Isolation disables SMTP, cron, webhooks, payment
requests, 1C integrations and other external egress. Potentially infected code must
not run inside the control plane's trusted web/API process.

**SEC-01 (P0).** On the captured copy, check official core/plugin checksums, custom
code changes against an explicitly trusted release, executables in uploads,
unexpected MU plugins/drop-ins, PHP/Nginx configs and suspicious patterns. Missing
official checksums mean unsupported, not passed. Compare custom code with an approved
artifact, not an automatically trusted latest backup. Mechanism sources:
[core](https://developer.wordpress.org/cli/commands/core/verify-checksums/),
[plugins](https://developer.wordpress.org/cli/commands/plugin/verify-checksums/).

**SEC-02 (P0).** Safely extract changes to administrators/roles, active components,
siteurl/home, schedules and important settings from the database. Reports must not
include passwords, session tokens or personal data. Mass deletion, size spikes,
new domains/redirects, missing backups and repeated errors are separate configurable
signals. Comparisons require a trusted baseline.

**SEC-03 (P0).** A finding includes severity, confidence, reason, files/digests,
first/last detection, investigation status and suppress-until with an explanation.
Automatic quarantine labels a point; it does not delete evidence or stop other
backups. A finding does not replace investigation, and its absence does not prove safety.

**SEC-04 (P1).** Optional ClamAV/YARA and vulnerability feeds, with pinned rule versions,
license accounting, resource limits and false-positive assessment. Checking known
vulnerabilities is not the same as detecting a compromise that already occurred.

**SEC-05 (P1).** System logs, SSH accounts/keys, cron/systemd and listeners use a
separate read-only sensor with separately granted privileges. The product explicitly
states that site-level scans do not fully cover the VPS or root compromise.

## 9. Restoration wizard

**RST-01 (P0).** Select a point and check completeness, keys and integrity; then select
a registered target or enter address/port/username/root password or SSH key,
passphrase and sudo password where needed. Secrets travel only over TLS, are not
returned to the browser and are not retained by default. Credential retention is a
separate choice with scope and expiry. The product must not enable root/password SSH
if the server forbids it; offer an allowed SSH key or sudo login instead.

**RST-02 (P0).** Inventory the target before any changes. Classes:
`clean_supported`, `wordops_compatible`, `wordops_needs_review`, `conflicting_stack`,
`unsupported`. Check OS/architecture, ports, disks/inodes, versions/extensions,
databases/access, existing sites, domains/aliases, external mounts and reboot needs.
An unknown OS or another panel must not be “fixed” by automatic removal.

**RST-03 (P0).** A human-readable plan includes the source point, target identity,
create/clone/replace mode, domains, resources, changes, secrets strategy, compatibility
conditions, checkpoints, data loss, manual actions and rollback. Bind the plan to the
inventory digest, fingerprint and expiry. Changing the target or plan invalidates
approval. Applying requires reauthentication and domain entry for replacement;
approval binds to a specific plan ID/hash.

**RST-04 (P0).** A clean VPS may receive a validated WordOps release from a pinned
source and components matching a compatible profile. On an existing VPS, do not
silently upgrade/downgrade MariaDB/Nginx, reinstall the stack or alter shared Redis.
If hosting the site would put neighbors at risk, propose another VPS or a separate
administrative plan outside restoration.

**RST-05 (P0).** Create/clone provisions a separate database, database user, docroot
and vhost through the WordOps adapter. Restore the agreed site settings, not all of
`/etc` or the old VPS root keys. Render verifiable configs for the target and retain
the originals as reference material. Nonstandard snippets require review.

**RST-06 (P0).** Replacement acquires a lock, revalidates the plan, pauses writes,
creates and verifies an independent pre-restore checkpoint of current files/database/
config, then prepares staging and switches over after checks. Without a checkpoint,
replacement is blocked. Do not change the shared `/var/www` or neighboring databases.
A partial failure restores the selected site or leaves it in explicitly managed
maintenance with precise recovery instructions; never report a false completed state.

**RST-07 (P0).** Full database replacement destroys data written after the selected
point. The UI shows its timestamp and an explicit orders/users warning. Automatic
WooCommerce merging is not provided. DB-only/files-only restoration is an advanced
mode with compatibility checks and its own checkpoint, and is not presented as full.

**RST-08 (P0).** Clone/domain changes use serialization-safe URL replacement with
exclusions and a report. Generate database credentials for the target and new salts
by default. SMTP/payment/1C secrets follow a policy: preserve target, restore source
or disabled; previews/tests always use disabled. No email, cron or external
integrations before confirmed cutover.

**RST-09 (P0).** Before DNS cutover, verify the site with the correct Host/SNI and
local override, Nginx config, PHP, database and reference pages; HTTP 200 alone is
insufficient. TLS has a separate plan: temporary private preview, certificate
issuance/verification, then public readiness. ACME HTTP requires domain routing;
without it, do not claim public TLS is ready. Do not change DNS automatically.

**RST-10 (P0).** Use a durable state machine, step journal and checkpoints, safe
retries, cancellation at permitted boundaries and manual recovery after reboot or
worker loss. After cutover, rollback needs a new decision: the site may already
have accepted writes. Cancellation does not automatically delete a ready site or
roll back shared packages.

**RST-11 (P0).** By default, a suspicious point may only be restored to an isolated
target. A production exception requires an administrator override, reauthentication,
a reason and a retained report. Root access must not execute archived PHP, shell
hooks or backup SQL with global privileges.

## 10. Web UI and reports

| Screen | Main actions and data |
|---|---|
| Overview | Unprotected sites, stale backups, checks, incidents and jobs |
| Servers | Registry, connectivity, capabilities, inventory diffs, enrollment/revocation |
| Sites | Coverage, dependencies, versions, plans and server-migration history |
| Plans | Contents, schedule, next run, timezone, retention and limits |
| Storage | Availability, quotas, capabilities, encryption and key recovery |
| Recovery points | Site/date filters; scope, age, completeness, pins and findings |
| Restoration | Point/target selection, inventory, plan diff, approval and steps |
| Verification | Scope, results, evidence, restore tests and read coverage |
| Jobs and audit | Progress, retries, steps, initiator, safe logs and exports |
| Settings | Users/roles, MFA, secrets, notifications and recovery kit |

**UI-01 (P0).** Provide filters and links between objects, keyboard accessibility,
a responsive interface, times with timezone, and English/Russian. Progress reflects
measured stages/bytes; unknown duration must not be hidden behind a fabricated percentage.

**UI-02 (P0).** SMTP and generic webhook notifications with retry/deduplication cover
errors, stale backups, integrity failures, critical findings, completed restores
and unavailable storage. No secrets/dumps in payloads. Notification delivery is
separate from backup success, but delivery failures remain visible. Channel setup
includes a test action.

## 11. Nonfunctional requirements

**NFR-01 (P0).** An external Linux VPS/VM with persistent workers, SSH egress, HTTPS UI,
private persistent staging and database. Proposal: Docker Compose initially; the
control host must not be a protected VPS. PHP-only shared hosting is unsupported.
Disk sizing accounts for the largest concurrent staging/restore operations, database
dumps, decryption and safety checkpoints; the UI blocks work when space is insufficient.

**NFR-02 (P0).** Session security, MFA for privileged actions, CSRF protection, rate
limiting, API RBAC, SSH host-key pinning, redaction, and defenses against shell/path/
argument injection, archive traversal, symlink escape, decompression bombs and SSRF
to metadata endpoints. Administrators explicitly allow private CIDRs if needed for
VPS or storage access.

**NFR-03 (P0).** The API does not run SSH/archive operations within the HTTP request
lifecycle. Workers use leases/heartbeats and an idempotent step journal. Logs and
metrics contain no secrets. Audit is append-only at the application level, with
export; this does not promise immutability against control-host root. A separate
heartbeat monitors the scheduler itself.

**NFR-04 (P0).** Formats and adapter protocols are versioned. New versions read all
previously supported formats within the first major release. Control-plane upgrades
include a database backup, migration, documented rollback and old-point restoration tests.

**NFR-05 (P0).** Preliminary benchmark profile: 10 VPS instances, 100 sites, up to
50 GiB of files and 5 GiB of database per site; a 4-vCPU/8-GiB-RAM control host with
separately sized disk. This is a target test profile, not a guaranteed limit or RTO.
The first compatibility target is Ubuntu 24.04 amd64 with a validated WordOps release;
exact PHP/MariaDB and source-to-target combinations are recorded after the spike.
Do not claim support for other OS/version combinations based only on upstream lists.

## 12. Success metrics and acceptance

| Metric | First-release criterion |
|---|---|
| Point completeness | No damaged/incomplete test dataset is published as complete |
| Neighbor preservation | All create/replace tests preserve reference hashes/configs/databases of neighboring sites |
| Disaster recovery | Every claimed source-to-target combination restores without the source |
| Control-plane recovery | Catalog/keys recover from kit and storage without the previous control database |
| Security state | Every seeded indicator yields a finding; unsupported checks never become passed |
| Secrets | Canary secrets are absent from API responses, process arguments, logs and public artifacts |
| Alerts | Stale backups are detected within two monitoring intervals; the default interval is 5 minutes |
| Recovery objectives | Plans store RPO; RTO is measured from start to verified serving and separately to public cutover |

The full scenario set, failure injection and release gates are in the [roadmap](roadmap.md).
There is no universal “one-minute recovery” promise: RTO depends on data volume,
bandwidth, storage, package installation, TLS and DNS actions.

## 13. Priorities, risks and open decisions

P0 is mandatory for the first stable release, including FTP and both target modes.
An intermediate alpha may be S3-only; it must not be presented as the complete product.
P1 covers stronger storage protection, system sensors and additional engines/adapters.

Critical risks: centralized credentials for all servers; untrusted archives;
non-atomic database/file capture; incompatible versions; shared WordOps configuration
changes; retention with deduplication; false confidence from malware checks.
Mitigations and residual risks are in the [threat model](threat-model.md).

Proposed, not yet approved: Go backend/workers, PostgreSQL, TypeScript web UI;
Restic for S3; a separate FTP bundle format; MIT for original code; single-organization
deployment. WordOps compatibility, strict consistency, FTP and existing-site rollback
spikes are mandatory before implementation. External commercial malware/vulnerability
feeds and DNS providers have not been selected.

The public repository contains only generalized requirements and synthetic examples.
Do not copy real sites, IP addresses, passwords, keys or dumps into it.
