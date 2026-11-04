# Implementation review and plan

Date: 2026-11-04. Based on the current PRD, landscape, architecture, threat model,
ADR 0001 and AC-01–35. This is a specification review, not product-trial evidence.

## Assessment of current tasks

The project's strengths are recovery after losing the VPS or control plane,
explicit privilege boundaries and separate integrity/consistency/security states.
The main risk is building a large control plane before validating WordOps restore
and FTP. G0 must justify an implementation choice, not merely list tools studied.

| Priority | Observation | Proposed action and verification |
|---|---|---|
| Blocks G1 | G0 lists topics without fixing inputs, protocols or evidence | Establish G0-00–08 below; each result includes versions, reproducible steps, expected/actual, evidence digests and verdict |
| Blocks selection | Landscape recommends a custom control plane before hands-on comparison | Compare adopt/integrate/build against identical ACs, including adapter and maintenance cost; `unknown` is not a competitor failure |
| Blocks safety | The backup account has no write access, but quiesced capture must stop writers | Separate read/export from a narrow freeze capability; test target-side watchdog, TTL and restoration of the exact original states |
| Blocks safety | Worker leases do not sufficiently describe stale-worker behavior after a partition | Test fencing generation and revalidation at helper/storage boundaries; stale workers cannot publish/cut over after takeover |
| Blocks format selection | AEAD and checksums do not determine who may publish recovery manifests | Choose a trusted commit/catalog protocol binding site/point/parts/key ID; test forged/replayed manifests and discovery without control DB |
| Blocks recovery | GitHub independence is specified, but clean-VPS bootstrap depends on package availability | Separate plugin-file restoration from stack provisioning; test local cache/mirror and pinned install artifacts, and document permitted external dependencies |
| Blocks replacement | Neighbor hashes/configs do not prove absence of downtime or lost writes | Use continuous neighbor HTTP and DB-write probes, reload failure and shared PHP/DB constraints; bind checkpoint/rollback to the moment writes reopen |
| Before G2 | The illustrative manifest lacks an executable schema and migration rules | After G0, specify a versioned schema, mandatory fields, unknown-version rejection and adversarial fixtures; do not treat draft JSON as a storage format |
| Before G2 | RPO is a goal, but its parameters and queue degradation are underspecified | Add RPO to the plan/API/UI contract and backlog/freshness/clock-skew policy; measure feasibility on fixtures, not just a schedule |
| Throughout | Security assurance is deferred to G4 although dangerous parsers/helpers arrive earlier | Add negative scope, secret, path/SQL and privilege-boundary tests alongside their G1–G3 components; G4 is the final assessment |
| Before G3 | FTPS is listed with FTP, but TLS failures have no distinct AC | Test invalid/expired certificates, hostname mismatch, no silent downgrade, data-channel TLS and passive mode; legacy FTP is an explicit separate profile |
| Before G1 | In-memory bootstrap secrets and durable jobs need a consistent model | On worker loss, discard the temporary credential and request it again; do not put it in the queue for retry |
| Pilot | No quantified demand or owner-defined RPO/RTO | Validate the actual workflow and acceptable downtime with an operator using synthetic scenarios; do not invent deadlines |

These recommendations refine contracts. They do not revise the PRD's meaning or
remove mandatory capabilities. Protected copy remains P1 with its documented residual
risk; its absence must not be hidden by immutable or ransomware-proof P0 claims.

## G0: minimum evidence and order

Execution needs explicitly designated disposable lab targets, a cost limit, allowed
addresses and a cleanup plan. This preparation does not authorize production work.
The first profile is Ubuntu 24.04 amd64; WordOps/PHP/database releases are selected
and pinned after actual successful runs. No combination is currently declared supported.

Minimum lab: a WordOps source, a clean target, an existing target with the restoration
site and two neighbors, a separate control host/staging area, and test S3 and FTP/FTPS
endpoints. VMs can be reused after reset between runs; source-loss tests must actually
make the source unavailable, without a hidden shared-disk dependency.

Fixtures: standard WordPress, WooCommerce with synthetic orders, cron/queue/external
writers, dynamic wp-config, registry/vhost drift and safe seeded indicators.
Start with small datasets for fault injection; the 50-GiB/5-GiB and 100-site profile
is a later capacity measurement, not a mandatory cost for every G0 run.

| Work | Depends on | Output and exit criterion | PRD / AC |
|---|---|---|---|
| G0-00: protocol and lab | — | Pinned versions/digests, reproducible fixtures, network/cleanup policy, evidence format, initial baseline | NFR-02/05; AC-26/33 |
| G0-01: adopt/integrate/build | 00 | Reaver, Backrest and Duplicati on identical scenarios; API/license constraints with primary links; required-adapter assessment; no scoring that hides hard blockers | S1–S6; AC-01/03/15/17/18/31 |
| G0-02: WordOps inventory and access | 00 | Actual CLI/config capture, capability matrix, no PHP eval, no cross-site/shell/restore access for backup keys; precise unsupported cases | REG-01–05, BKP-04; AC-01–04/20/33 |
| G0-03: consistency and freeze | 02 | Honest online drift reporting; stopped quiesced writers; kill/partition/reboot/cancel restores original states or reports needs_operator; unknown writers block strict mode | BKP-05/06; AC-09/10/24/35 |
| G0-04: storage and publication | 00 | Compare Restic S3, Restic+rclone FTP, standalone bundles and Duplicati reuse; no false complete under quota/truncation/list delay/no rename/concurrent operations; FTPS certificate failures | STO-01–05, BKP-07/08; AC-07/08/11–13 |
| G0-05: keys and control-plane loss | 04 | Storage+offline kit rebuild the catalog on an empty control plane; handle old/new keys and incomplete/orphan points; plans disabled | S6, STO-04/05; AC-31/32 |
| G0-06: clean/create/replace | 02/03/04/05 | Clean restore without source; create/clone/replace with checkpoint, stale-plan rejection, fault injection and neighbor probes; rollback boundary after writes reopen | RST-01–11; AC-05/15–25/30/35 |
| G0-07: isolation and security sketch | 02, then 06 | Helper privilege diagram; safe indicators yield findings, not_checked is not passed; restored runtime has no egress, evidence contains no secrets | VER-01–03, SEC-01–03, NFR-02; AC-26–30/33 |
| G0-08: decision | 01–07 | Evidence summary, compatibility matrix, selected path and rejected alternatives, updated ADR, qualified cost estimate, unmet-requirement list | All G0 conditions |

After 00, work on 01, 02 and 04 can proceed independently. The earliest useful result
is inventory → full capture → source/control-database loss → restore → replacement
with a failure. Do not build the full scheduler/UI before this result. Engine choice
depends on restoration as well as successful storage uploads.

## Evidence format

Use the [experiment template](research/experiment-template.md). Required: ID and
hypothesis; requirement/AC IDs; UTC run time; versions and artifact digests; synthetic
fixture; topology; reproducible commands; expected/actual per scenario; fault point;
exit codes; cleanup; CPU/RAM/disk/network/pause/RTO measurements with conditions.
Results: `planned`, `documented`, `tested-pass`, `tested-fail`, `blocked`, `unknown`.
Only `tested-pass` closes a technical criterion. A report without a real run must
not contain fabricated measurements or tested versions.

Public results contain only synthetic artifacts checked for leaks. Vendor claims
are labeled documented. Comparisons use the same inputs; an unavailable trial means
blocked/unknown, not a claim that the product does not support the capability.

## G0 decision

1. **Adopt**: an existing open product meets hard requirements and verifiable recovery
   without a mandatory paid service; its operational limitations are accepted.
2. **Integrate**: extensions/APIs can cover WordOps inventory, privilege boundaries,
   S3/FTP and safe restoration without a risky fork; assess upgrades and recovery dependencies.
3. **Build orchestration**: the first two paths have evidenced blockers or greater
   measured maintenance cost; continue reusing storage/crypto implementations.
4. **No-go / reconsider**: safe replacement, FTP recovery or key recovery is unproven.
   Explicitly state the unmet requirement; do not silently reduce stable scope.

The gate requires all mandatory evidence, not an average score. An unknown critical
outcome blocks the final decision. ADR 0001 changes status only after this summary
and a decision accepted by the project owner.

## Implementation after G0

| Stage | End-to-end outcome | Acceptance before the next stage |
|---|---|---|
| G1 | Minimal web UI → auth/MFA/RBAC → registry → host-key-pinned read-only inventory; then helper enrollment and durable jobs | Two lab servers, scoped permissions, secret canaries, host-key mismatch, restart/fencing; separate bootstrap plan |
| G2 | One site → full capture → S3 → catalog → isolated restore; then schedules, partial modes, retention and freshness | AC-05–10/13/14/31/33/34; orphan reconciliation; UI shows separate assurance states honestly |
| G3 | FTP/FTPS and clean/existing create/clone/replace through plan approval; quiesced profiles only for validated writers | AC-11/12/15–26/30–32/35 and G2 regression; neighbors, checkpoint, TLS, source/control-plane loss, old recovery points |
| G4 | Expanded static/database findings, scheduled drills, performance, RU/EN/accessibility, packaging/runbooks | All P0/AC-01–35, independent helper/parser security review; reproducible recovery kit and measured RPO/RTO |
| G5 | Protected copy/Object Lock, wider matrix and adapters | Separate P1 decisions, no implicit production-scope expansion |

Split each stage into small AgentMarshal contracts with a specific OpenSpec change,
scope, negative tests and evidence. Maintain the shared threat model from the first
executable component. Set timelines and the application stack after G0, once the
custom-code scope, team and measurements are known; this table is not a calendar plan.

## Next action

Execute G0-00: agree on disposable lab targets and the experiment protocol, pin
fixtures and release inputs. Then start G0-01/02/04. Tooling setup and planning do
not complete any of these experiments.
