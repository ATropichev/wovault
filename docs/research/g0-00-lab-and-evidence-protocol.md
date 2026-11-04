# G0-00 — lab and evidence protocol

Status: **executed on the `local-namespace` profile** (2026-11-04, second
repair round). The container and remote-VPS profiles are defined but not
activated — no Docker socket or target authorization exists in this
environment, and this report does not claim them. This document records the
lab protocol required by task 1 of
`openspec/changes/validate-g0-feasibility/tasks.md`; it is the first group
only and does not complete G0 or select any architecture, engine or
supported version.

## Hypothesis and criterion

- Requirement IDs / AC IDs: NFR-02, NFR-05, VER-01, VER-03, RST-08; AC-26,
  AC-33. The protocol itself is a precondition for every later AC-01–35 run.
- Claim under test: a disposable synthetic lab can (1.1) enumerate authorized
  targets while refusing production-shaped resources, (1.2) regenerate
  byte-identical pinned fixtures, (1.3) validate machine-readable evidence
  that rejects missing fields and never promotes `unknown`/`blocked` to
  passed, and (1.4) prove runtime isolation, baseline reset and canary
  hygiene with actual runs — all without any production, cloud or credential
  access.
- Failure condition: protocol checks that require forbidden access, or
  checks that report success without real isolation/enforcement.
- Product under test: WOVault G0 lab tooling in `lab/` (this repository);
  there is no third-party product or vendor claim under test.

## Reproduction

- UTC run time and run ID: `2026-11-04T12:36Z`; reports
  `lab/evidence/runs/g0-00-targets.json` (sha256 `4e6b44c3…`),
  `g0-00-fixtures.json` (`d050058f…`), `g0-00-evidence-schema.json`
  (`3a421190…`), `g0-00-isolation-reset-canary.json` (`bd63a466…`).
- Fixture generator/commit and input digests: `lab/fixtures/generate.py`,
  inputs `lab/fixtures/pins.json` (sha256 `24d89b25…`, spec 1). Expected
  manifests in `lab/fixtures/expected/`: site-alpha `ad50e24a…`,
  neighbor-beta `ba0a6283…`, neighbor-gamma `260fe088…`.
- Versions and topology: Linux x86_64, kernel `6.6.87.2-microsoft-standard-WSL2`,
  Python 3.13.5, bwrap 0.12.0, unshare (util-linux 2.41.5); Docker client
  present, daemon unreachable. Single `local-namespace` target
  `local-sandbox`; roles and documentation-range identifiers in
  `lab/topology.md`.
- Authorized disposable targets and reset/cleanup: `lab/targets.json`
  (`targets`: `local-sandbox` only; `pending_targets`: `wov-g000-containers`,
  `wov-g000-vps-pair`, both `authorized=false`). Ownership boundary in
  `lab/resources.json` (`lab-output/` paths, `wov-g000-*` container names).
- Synthetic addresses, resource limits, network policy: RFC 5737 ranges
  192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24 as identifiers only; ≤4
  targets, ≤2 GiB disk/RAM, ≤64 MiB fixtures, ≤300 s/check; zero external
  egress.
- Exact commands (from repo root, Python ≥3.12, no third-party packages):

```sh
python3 lab/tools/labctl.py verify-allowlist
python3 lab/fixtures/generate.py generate && python3 lab/fixtures/generate.py --check
python3 lab/evidence/validate.py --selftest
python3 lab/tools/run_checks.py all           # emits the four run reports
python3 lab/tools/labctl.py scan --paths lab/evidence lab docs
python3 lab/tools/labctl.py cleanup --apply   # removes lab-output/
```

## Observations

Every verdict below is copied from the machine-readable reports; each
`tested-pass` scenario carries its command output artifact and sha256 inside
`lab/evidence/runs/<report_id>/`, and validation verifies that each recorded
path exists and matches its digest.

| Scenario / fault point | Expected | Actual / exit code | Evidence | Verdict |
|---|---|---|---|---|
| 1.1 `allowlist-verify` | all executable targets disposable+authorized, no production addresses | exit 0; executable=`local-sandbox`; 2 pending non-executable | `g0-00-targets/verify-allowlist.json` | tested-pass |
| 1.1 `allowlist-rejects-production` | doctored allowlist (non-loopback `192.0.2.99`) rejected | exit 2, forbidden address listed | `g0-00-targets/verify-doctored.txt` + doctored input | tested-pass |
| 1.1 `pending-target-not-executable` | `labctl resolve` refuses pending container target | exit 3 (refused) | `g0-00-targets/resolve-pending.txt` | tested-pass |
| 1.1 `cleanup-refuses-unowned` | `cleanup --apply` on a tracked file refuses and leaves it intact | exit 3; file unchanged | `g0-00-targets/cleanup-refuse.txt` | tested-pass |
| 1.1 `cleanup-refuses-symlink-escape` | a symlink inside `lab-output/` pointing outside is refused | exit 3; `docs/` intact | `g0-00-targets/cleanup-symlink-refuse.txt` | tested-pass |
| 1.1 `containers-require-activation` | `cleanup --containers` refuses while the container target is pending, incl. remote `DOCKER_HOST`/context probes, without daemon contact | exit 3 (refused) on all four probes | `g0-00-targets/cleanup-containers-*.txt` | tested-pass |
| 1.1 `generate-out-refuses-unowned` | fixture `--out` outside the owned prefix and through a symlinked ancestor refused; nothing created | exit 3 both; `/tmp` target absent | `g0-00-targets/generate-out-*.txt` | tested-pass |
| 1.1 `workdir-refuses-unowned` | `run_checks --workdir`/`--publish` outside owned scopes refused before creation | exit 3 both; dirs absent | `g0-00-targets/workdir-refuse.txt`, `publish-refuse.txt` | tested-pass |
| 1.2 `generate-repeatable` | two generations byte-identical | 3 fixtures, identical manifests/digests | `g0-00-fixtures/repeatability.txt` | tested-pass |
| 1.2 `matches-pinned-manifest` | regeneration equals `fixtures/expected/` | MATCH ×3 | `g0-00-fixtures/pinned-check.txt` | tested-pass |
| 1.2 `synthetic-content-only` | only doc-range IPs and example/invalid domains in trees | 0 violations in 136 files | `g0-00-fixtures/synthetic-scan.txt` | tested-pass |
| 1.2 `canary-placement` | canaries only where pinned (site-alpha 3, neighbors 0) | as expected | `g0-00-fixtures/canary-placement.txt` | tested-pass |
| 1.3 `schema-document-loads` | schema JSON parses; verdict enum + conditionals present | 6 verdicts, 4 conditional rules | `g0-00-evidence-schema/schema-load.txt` | tested-pass |
| 1.3 `selftest-passes` | 2 `valid-*` accepted, 23 `err-*` rejected | 25/25 correct | `g0-00-evidence-schema/selftest.txt` | tested-pass |
| 1.3 `missing-fields-rejected` | report missing required fields rejected | exit 2, fields named | `reject-missing.txt` | tested-pass |
| 1.3 `pass-without-run-rejected` | `tested-pass` without actual/evidence rejected | exit 2 on both vectors | `reject-fabricated-*.txt` | tested-pass |
| 1.3 `unknown-is-not-a-pass` | `unknown` validates but counts 0 tested-pass; `unknown`+actual rejected | verified | `unknown-summary.txt`, `reject-unknown-run.txt` | tested-pass |
| 1.3 `unauthorized-target-rejected` | report naming a non-allowlisted target rejected | exit 2 | `reject-target.txt` | tested-pass |
| 1.3 `canonical-schema-agreement` | canonical validator never accepts a schema-invalid report | 25/25 examples agree; canonical-stricter cases are the documented allowlist and artifact-filesystem cross-checks | `schema-agreement.txt` | tested-pass |
| 1.3 `evidence-content-required` | empty `command`/`stdout` evidence rejected | exit 2 on both | `reject-empty-*.txt` | tested-pass |
| 1.3 `artifact-existence-verified` | missing, escaped or digest-mismatched artifact paths rejected; same file structurally valid under `--no-artifact-check` | exit 2 on all four; exit 0 without the check | `reject-artifact-*.txt`, `artifact-check-disabled.txt` | tested-pass |
| 1.3 `assurance-dimensions-explicit` | missing/incomplete assurance and unbacked passed/failed/warning rejected; valid example's dimension-linked pass accepted | exit 2 ×4, exit 0 valid | `reject-assur*.txt`, `valid-assurance.txt` | tested-pass |
| 1.4 `net-egress-denied` (AC-26) | all TCP egress and DNS fail in the unshared net namespace | 5×ENETUNREACH, 2×DNS fail; netns differs | `payload-result.json` | tested-pass |
| 1.4 `fs-write-confined` | writes succeed only inside the bound docroot | `/site` ok; `/`, `/etc`, `/usr`, `/tmp`, `/proc`, `..` all EROFS/ENOENT | `payload-result.json` | tested-pass |
| 1.4 `namespace-confidentiality` | host sentinel/host files unreadable, marker env absent, only sandbox PIDs visible, sentinel intact, no strays | all confirmed; pids=[1,2] | `payload-result.json` | tested-pass |
| 1.4 `baseline-reset-restores` | reset returns mutated working copy to baseline | `matches_baseline=true`; strays removed | `reset.json` | tested-pass |
| 1.4 `reset-refuses-unowned` | reset refuses `docs/` | exit 3 (refused) | `reset-refuse.txt` | tested-pass |
| 1.4 `reset-refuses-overlap` | reset refuses scope/baseline pairs where one contains the other | exit 3 both directions; baseline intact | `reset-overlap-refuse*.txt` | tested-pass |
| 1.4 `canary-leak-detected` (AC-33) | scanner flags every pinned canary in a raw artifact | 3/3 ids detected, exit 1 | `scan-raw.json` | tested-pass |
| 1.4 `canary-redaction` (AC-33) | sanitized artifact scans clean | exit 0 after `redact` | `job.sanitized.log`, `scan-sanitized.json` | tested-pass |
| 1.4 `scan-incomplete-coverage` | missing path/unreadable file → exit 2 (non-success); binary canary → hit; clean dir → 0 | as expected | `scan-coverage-*.json` | tested-pass |
| 1.4 `reports-carry-no-canary` | no canary value under `lab/evidence/` | 0 hits, 0 errors | `scan-reports.json` | tested-pass |
| 1.4 `no-workstation-paths-in-evidence` | no absolute repo/home prefix in retained artifacts | 0 offenders | `workstation-path-scan.txt` | tested-pass |
| 1.4 `container-isolation-profile` | same checks inside `wov-g000-*` containers | no Docker socket; coordinator-run | — | **blocked** |

Totals: **33 tested-pass, 0 tested-fail, 1 blocked, 0 unknown** across 34
scenarios. The blocked scenario is not a pass and is not counted as evidence
of container behavior; it requires the coordinator-run profile in
`lab/README.md`.

## Measurements and decision

- Fixture: 3 synthetic sites, 68 files per tree (~60 KiB) — deliberately
  small per the plan; the 50 GiB/5 GiB profile is a later capacity run.
  Generation wall time <1 s; bwrap payload run ~25 ms; whole suite <5 s
  (durations are per-scenario `duration_ms` in the reports, measured not
  fixed).
- Assurance states: `transfer`, `completeness`, `consistency`, `integrity`,
  `restore_test`, `security` are all **not_checked** in every report — G0-00
  runs protocol checks, not a backup, and the schema now requires all six
  dimensions to be declared explicitly.
- Neighboring-site state and cleanup: every report carries a `cleanup`
  block; this run recorded `performed=true, verified=true` with each group's
  workdir removed (`--no-cleanup` instead records the retained path
  explicitly). The repo canary scan found values only in
  `lab/fixtures/pins.json` (their definition site). No host file outside
  `lab-output/` was modified; the planted host sentinel was intact and no
  strays appeared outside the confined docroot.
- Limitations: (a) `local-namespace` isolation is a real kernel namespace
  boundary (mount, network, PID, UTS, IPC, user) but not a VPS/hypervisor
  boundary; (b) the payload is cooperative — it demonstrates that the
  harness can *observe* denials, not resistance to a determined in-namespace
  attacker; (c) fixtures are synthetic stand-ins — nothing here pins or
  validates real WordOps/WordPress/PHP/MariaDB versions; (d) container and
  remote profiles produced no evidence (`blocked`), so any later claim
  needing them is unproven; (e) artifact verification proves recorded files
  exist and match their digests at validation time — it cannot prove the
  recorded runs were honest, only that the evidence is consistent.
- Implications for adopt/integrate/build: none directly — G0-00 is a
  precondition. It unblocks G0-01/02/04 *local* runs with pinned inputs and
  a digest-pinned evidence format whose artifacts are verified at
  validation; engine and architecture remain undecided.
- Public-inclusion check: all artifacts are synthetic — example domains,
  documentation IPs, `WOVAULT-CANARY-*` tokens referenced by id only;
  retained evidence records repository-relative paths only, and saved
  artifacts have the repo/home absolute prefixes sanitized before their
  digests are computed. No credentials, customer data or real inventories
  were accessed or produced.
- Protocol corrections after the first independent review: resource
  ownership is enforced on the resolved path against the lexical owned
  prefixes; `reset` refuses overlapping scope/baseline pairs; container
  cleanup reports failed removals as leftovers with `verified=false`; the
  canonical validator rejects everything the published schema rejects
  (differential evidence in `schema-agreement.txt`).
- Protocol corrections after the second coordinator review: every mutating
  destination (`generate --out`, `run_checks --workdir`, `redact --out`) is
  validated on its resolved path before creation/deletion, and evidence
  publication is scoped separately to `lab/evidence/runs/`; container
  cleanup now requires an activated container-set target plus the approved
  local Docker endpoint and refuses without daemon contact while pending;
  the isolation payload runs in a narrowed namespace (read-only root
  skeleton, cleared environment, `--unshare-all` including PID) and setup
  failures — like the NETLINK_ROUTE denial observed in the coordinator's
  environment — are classified `blocked`, not `tested-fail`; evidence
  entries must carry content (empty command references are rejected) and
  recorded artifact paths are verified for existence and digest at
  validation; all six assurance dimensions are declared explicitly and a
  checked state requires a dimension-linked tested scenario; the canary
  scan is byte-based and reports incomplete coverage as non-success; every
  group finalizes with a cleanup record on success, failure or exception,
  and `run_checks` exits non-zero on any `tested-fail` — a valid report is
  not the same as a successful experiment.

## Follow-up required before remote execution

- Coordinator runs the container profile (commands in `lab/README.md`) and
  records its own `g0-evidence/1` reports; image tags/digests are pinned by
  that run, not asserted here. Activation means moving
  `wov-g000-containers` from `pending_targets` into `targets` with
  `authorized=true` after confirming the cleanup plan.
- Named disposable VPS targets (addresses, budget, cleanup approval) need a
  separate explicit assignment; until then `wov-g000-vps-pair` stays
  `authorized=false` and lab tooling refuses it.
