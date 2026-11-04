# Threat model and access boundaries

Date: 2026-11-04 · Status: design requirements, not an audit report.

## Protected assets

Site and customer data; SSH/database/storage secrets; the ability to change production;
recovery-point history; decryption keys; trusted baselines; neighboring-site availability;
and the reliability of audit records and notifications.

## Trust boundaries

- Operator browser ↔ HTTPS API: every request is checked against RBAC and scope.
- API ↔ worker: the API submits a typed job, not an arbitrary shell command.
- Control plane ↔ VPS: host-key pinning; the source may already be compromised.
- Backup principal ↔ restore principal: separate capabilities and credentials.
- Site ↔ root helper: untrusted PHP/SQL must not become executable root code.
- Control plane ↔ storage: storage can lose/replace data; encryption does not replace retention.
- Archive ↔ parser/lab: contents may be hostile; network access and mounts are restricted.

## Risk matrix

| Threat | First-release mitigations | Residual risk |
|---|---|---|
| Stolen backup key | Forced command, site allowlist, no writes/restore, revocation | Read access to data from all permitted sites |
| Compromised UI account | MFA, RBAC, reauthentication, short sessions, separate restore approvals | Authorized roles can abuse their privileges |
| Compromised worker/control host | Service separation, secret scopes, separate keys, audit export | A running worker sees the secrets it needs; widespread damage is possible |
| Compromised production | Pull, no storage credentials on the VPS, external baselines | The source can return false data and hide evidence |
| SSH MITM | Verify fingerprint before credentials, pinning, block on change | Initial verification needs a trusted channel |
| Shell/path injection | Typed protocol, fixed argv, canonical paths, root-owned config | Parser/helper needs fuzzing and review |
| Archive traversal/symlink/device | Validate before extraction, safe extraction, limits, separate VM | Decompressor/runtime vulnerabilities remain possible |
| Malicious SQL/config | Least-privilege DB import, no PHP eval/root execution, runtime sandbox | The restored site may still contain malware |
| Deletion/encryption of new files | Versioned snapshots, pins, anomalies, separate retention queue | A damaged source produces a damaged new backup |
| Deletion of old backups | No storage keys on production; separate prune privileges | Control-plane/storage administrators can delete accessible copies; protected copy is P1 |
| Storage corruption | Authenticated manifests, engine checks, readback, restore tests | Checks consume time, space and egress |
| Lost master key | Offline recovery kit, tested import procedure | Decryption is impossible without a backup key |
| Target substitution before restore | Plan hash, inventory/fingerprint binding, revalidation | External races remain possible after checking; use site locks and repeated preconditions |
| Wrong site selected | UUID, domain confirmation, plan diff, checkpoint | A person may approve the wrong plan |
| Neighboring-site damage | Site-scoped actions, no stack upgrades, integration assertions | Shared services still create a shared failure domain |
| SSRF / metadata theft | Registered targets, CIDR allowlist, redirect policy, isolated scanner egress | Permitted private networks remain reachable within policy |
| Report/log leaks | Redaction, safe metadata, download permissions, retention | Backups contain personal data and need separate protection |
| Scheduler/notification outage | External heartbeat, freshness checks, visible delivery errors | Losing both the control plane and monitor requires external response |

## Privilege rules

Bootstrap/root credentials are allowed for inventory and approved preparation.
By default, they are retained only for the job's duration. Root passwords must not
appear in queue payloads, argv, exports or browser responses. Persistent administrative
credentials require an explicit administrator choice, encryption and TTL.

The backup helper permits file reads, database export and authorized inventory.
It must not let the user edit the allowlist, select arbitrary paths or replace
executables. Installing a root-owned helper includes checking every parent directory,
config owner and symlink; validate sudo configuration before changing its rules.

The restore helper has a separate command and capability. A UI plan is not sufficient
protection by itself: the server checks allowed operations, target site, expiry and
agreement with current state. Signatures/nonces prevent replay within the defined
protocol; local root on the target VPS remains above this boundary.

Blanket grants for `bash`, `python`, `rsync`, `tar` or unrestricted `wp` are forbidden.
Do not run `wp-config.php`, MU plugins or plugins as root to obtain a database password.
A shared `www-data` account cannot justify a promise of independent customer isolation.

## Suspicious-backup policy

Retain suspicious points with evidence and an incident pin. A new suspicious point
must not automatically cause trusted older points to be deleted. Acknowledging a
finding does not make an archive clean; baseline approval is a separate permission.

Production restoration of a suspicious point is blocked by default. An administrator
may override it with a reason after reviewing evidence, but that override cannot
bypass integrity failures: damaged data is only allowed in a separate forensic/export
workflow without a promise of successful restoration.

Checksum checks detect changes, not every intrusion method. A new vulnerability may
leave files unchanged; malicious records may be in the database; root compromise can
forge any VPS response. A serious incident calls for host isolation, preservation of
evidence and recovery into a trusted environment with credential rotation, rather
than relying on a green scanner result.

## Testing requirements

Use only synthetic fixtures and authorized lab VPS instances. Test traversal,
symlinks, special files, large archives, shell metacharacters, replay, cross-site
paths, host-key mismatch, secret canaries and scope bypasses. Verify that the backup
principal cannot change a site, restore metadata or another site's files.

Before the first stable release, separately review the SSH/sudo helper, credential
handling, bundle parser and restore state machine. Never upload real malware to the
public repository; use safe synthetic indicators and test signatures for detectors.
