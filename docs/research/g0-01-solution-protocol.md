# G0-01 — existing-product trials: licence/API inventory and shared protocol

Status: **documentary preparation completed under CR-003** (primary sources
read 2026-11-05). No product was installed, executed or restored; no release
or binary is selected. This document prepares the hands-on work for tasks
2.1–2.4 of `openspec/changes/validate-g0-feasibility/tasks.md`; those tasks
stay open, and nothing here closes G0, selects an engine or declares a
supported version.

## Evidence discipline and boundaries

- Repository/source inspection and vendor documentation are `documented`
  observations, not `tested` results. Only an actual run on an authorized
  disposable target can produce `tested-pass`/`tested-fail`; a missing
  prerequisite is `blocked`; a capability the sources do not describe is
  `unknown`. Verdict definitions follow
  [experiment-template.md](experiment-template.md) and the G0-00
  `g0-evidence/1` schema.
- The adopt/integrate/build/no-go boundary and every mandatory P0
  capability are preserved. An unverified capability is `unknown`, not a
  product failure; a vendor claim is `documented`, not `tested`.
- Web pages are mutable. Each observation carries its read date and, where
  available, an immutable source revision (a commit SHA). Mutable pages
  must be re-read before a hands-on contract relies on them.
- Cloud provisioning, paid trials, registration and production operations
  are not authorized; nothing was purchased, registered or installed for
  this report.

## Actual runs under this contract

Read-only HTTPS GET requests on 2026-11-05 (UTC). GitHub content came from
raw/API endpoints (file contents plus licence-detection metadata); Reaver
pages were fetched directly over HTTPS and returned HTTP 200. No product
binary, installer, agent or demo was downloaded or executed, and no account
or licence was created.

| Source | Immutable revision | What was checked |
|---|---|---|
| `github.com/garethgeorge/backrest` — `LICENSE` | commit `148ba12c12a7a4fef6d3c6c8e675ca2c5e7d3635` | licence text = GNU GPL v3 |
| same repository — `README.md`, `proto/v1/service.proto` | same commit | API surface and runtime dependencies at that revision |
| `garethgeorge.github.io/backrest/docs/api` | — (mutable page, read 2026-11-05) | which endpoints are documented as stable |
| `github.com/duplicati/duplicati` — `LICENSE` | commit `7d68b1f78df2a9152d188fa5e39ca9839a435ce4` | licence text and its carve-outs |
| same repository — `proprietary/LICENSE`, `Duplicati/WebserverCore/DuplicatiWebserver.cs` | same commit | bundled terms and API implementation detail |
| `api.github.com/repos/duplicati/duplicati/license` | — (mutable endpoint, read 2026-11-05) | GitHub licence detection = SPDX `NOASSERTION` |
| `api.github.com/repos/restic/restic/license`, `api.github.com/repos/rclone/rclone/license` | — (mutable endpoints, read 2026-11-05) | bundled dependency licences: BSD-2-Clause, MIT |
| `reaverbackup.com/terms`, `/pricing`, `/docs`, `/docs/rest-api`, `/docs/mcp` | — (mutable pages, read 2026-11-05) | licence tiers, API/MCP availability, agent model |
| `docs.duplicati.com` ServerUtil, FTP-destination and disaster-recovery pages | — (mutable pages, read 2026-11-05) | supported automation path; FTP verification/transport options; recovery without the original install |

## Licence and API observations

### Reaver Backup — commercial licence; API on paid plans (documented 2026-11-05)

No public source repository or source-level licence file was located, so
there are no repository terms to inspect; the licence instrument is the
vendor terms page (self-reported last update 2026-08-26). Release artifacts
were not selected or fetched.

- **Terms.** "Reaver Backup is commercial software": each tier grants a
  non-exclusive, non-transferable right within its site and destination
  limits. The Free edition is limited to **evaluation and non-commercial
  use**, **one site** and **local storage only**. Paid tiers add offsite
  destinations, the REST API and the MCP server. The terms prohibit
  redistribution, reverse engineering and providing a managed backup
  service to third parties. Anonymous product statistics default on with
  an opt-out; paid licences require registration.
  [Terms](https://reaverbackup.com/terms),
  [pricing](https://reaverbackup.com/pricing).
- **Architecture and API (documented, untested).** A self-hosted dashboard
  (UI, job queue, schedules, SQLite database) plus poll-only agents on
  protected hosts that run restic; agents accept no inbound API. WordPress
  installs can be auto-discovered and arbitrary paths added. The dashboard
  exposes `/api/v1` with `rv2_` bearer tokens (permissions
  `read`/`backup`/`restore`/`admin`), an install-local spec at
  `GET /api/v1/openapi.json` and an MCP endpoint `/api/v1/mcp`; restore
  calls require `confirm_slug`, and clean restore needs a finished
  preview. Both the REST API and MCP are advertised for paid plans only.
  Client-side restic encryption is optional and dashboard-managed.
  [Docs index](https://reaverbackup.com/docs),
  [REST API](https://reaverbackup.com/docs/rest-api),
  [MCP](https://reaverbackup.com/docs/mcp).
- **Repository vs release/bundled terms.** The agents run restic, so any
  distributed artifact plausibly carries restic (BSD-2-Clause) and other
  components under their own licences; verify per selected artifact once
  an installer is pinned.
- **Trial-permission consequence.** A Free licence covers only
  evaluation/non-commercial use of one site with local storage. The S1–S6
  suite needs multiple sites, offsite destinations and API access, so a
  full Reaver trial is `blocked` on a paid-licence and registration
  authorization that is not granted. Even an evaluation-scale probe still
  needs an authorized disposable target and a pinned installer.

### Backrest — GPL-3.0 source; gRPC/HTTP API (documented 2026-11-05)

- **Repository licence.** `LICENSE` at commit `148ba12c` is the GNU
  General Public License v3 (full text verified). A fork or embedded
  derivative carries GPL obligations plus upstream-maintenance cost, as
  already flagged in [landscape.md](landscape.md).
- **API.** `proto/v1/service.proto` at the same commit defines the
  `v1.Backrest` gRPC service: config read/write, repo add/check/remove,
  snapshot and file listing, `Backup`, `Restore`, `Forget`, `DoRepoTask`
  (index/prune/check/stats/unlock/forget), cancel, operation events and
  logs, arbitrary `RunCommand` and host pairing tokens. The docs page
  states endpoints are exposed over HTTP through a JSON-RPC gateway (e.g.
  `POST /v1.Backrest/Backup`) with basic auth or disabled authentication,
  and that **only the documented Backup and GetOperations calls are
  stable**; other endpoints and the operation schema may change.
  [API docs](https://garethgeorge.github.io/backrest/docs/api).
- **Bundled/runtime components.** The README at the pinned commit names
  restic as the sole dependency — auto-downloaded on first run or supplied
  by the system (`BACKREST_RESTIC_COMMAND`); the Docker image additionally
  includes rclone. Restic is BSD-2-Clause and rclone MIT (GitHub licence
  endpoints, 2026-11-05). The GPL file does not cover those components,
  and per-release artifacts were not selected — recheck bundled licences
  at pin time.
- **Trial-permission consequence.** GPL imposes no cost blocker; a trial
  still needs a pinned release and an authorized disposable target.

### Duplicati — MIT core with a proprietary subtree (documented 2026-11-05)

- **Repository licence.** `LICENSE` at commit `7d68b1f7` is MIT
  (Duplicati Inc., 2026) with explicit carve-outs: any `proprietary/`
  directory is under its own licence; incorporated third-party components
  keep their original licences; client-side JavaScript is MIT; everything
  else is MIT. GitHub licence detection returns SPDX `NOASSERTION` — do
  not describe the whole repository or every release component as MIT.
- **Bundled terms at the same commit.** `proprietary/LICENSE` exists and
  is a subscription instrument: production use of the covered parts
  requires a valid Duplicati Inc subscription for the correct features and
  seats; MIT applies only to parts distributed as "Duplicati Inc OSS" or
  as client-side assets. Any integration assessment must first enumerate
  which planned touchpoints resolve to `proprietary/` paths.
- **API.** `Duplicati/WebserverCore/DuplicatiWebserver.cs` at the pinned
  commit shows an ASP.NET Core (Kestrel) server with JWT bearer
  authentication and Swagger/OpenAPI registration gated behind `#if
  DEBUG` — disabled in release builds — with versioned v1/v2 DTO surfaces.
  In [issue #4201](https://github.com/duplicati/duplicati/issues/4201) the
  maintainer confirms Swagger is off in release builds, that the API may
  change, and that `duplicati-server-util` is the supported scripted
  path. The ServerUtil docs cover login/refresh-token handling,
  list/run/export/import of backups, pause/resume and health/status.
  [ServerUtil](https://docs.duplicati.com/duplicati-programs/command-line-interface-cli-1/serverutil).
- **Storage/recovery docs.** The FTP destination documents verification
  and transport options
  ([FTP destination](https://docs.duplicati.com/backup-destinations/standard-based-destinations/ftp-destination));
  the disaster-recovery page documents direct restore without the original
  installation and `Duplicati.CommandLine.RecoveryTool` for damaged
  backends
  ([disaster recovery](https://docs.duplicati.com/using-tools/disaster-recovery)).
- **Repository vs release.** Release installers bundle a .NET runtime and
  third-party libraries under their own licences; combined with the
  `proprietary/` subtree, a per-artifact licence inventory is required for
  whichever release is pinned.

## Shared S1–S6 trial protocol

### Fixture and topology

Inputs are the G0-00 pinned synthetic fixtures (`lab/fixtures/pins.json`,
spec 1, sha256 `24d89b25…`, seed `wovault-g0-00-fixture-seed-2026-11-04`):

- `site-alpha` (role `restore-site`): WooCommerce-style orders, writers
  `cron`/`queue`/`external-importer`, drift records
  `registry-domain-mismatch` and `vhost-alias-unregistered`, and the three
  `WOVAULT-CANARY-*` tokens (referenced by id only).
- `neighbor-beta` and `neighbor-gamma` (role `neighbor-site`): reference
  sites whose hashes, configs and databases must survive the S4 probes.
- Topology roles (documentation-range identifiers only): `source`
  192.0.2.10, `clean-target` 192.0.2.20, `existing-target` 192.0.2.30,
  `control` 198.51.100.10, `storage-s3` 198.51.100.20, `storage-ftp`
  198.51.100.30.
- `simulated_versions` (WordPress 6.8.1, WooCommerce 9.4.2, WordOps
  3.22.1, PHP 8.3.14, MariaDB 10.11.10, Nginx 1.26.2) are metadata
  labels, **not** validated upstream versions and imply no support claim.

These generated file trees are **synthetic stand-ins**. They can verify
protocol mechanics — evidence schema, allowlist enforcement, canary
hygiene, verdict discipline — but cannot qualify application restore,
WordOps compatibility or version support. Qualification needs a real
WordPress/WooCommerce fixture, including a database and writer processes,
on a pinned disposable WordOps stack; selecting and pinning that stack
and its install artifacts is an explicit prerequisite outside this
document.

### Protocol steps (identical for each product)

Each executed probe must produce a schema-valid `g0-evidence/1` report
with requirement/AC mapping, expected/actual, evidence digests, an
explicit verdict and a cleanup record. Primary ACs are the shared
differentiator suite from the roadmap and tasks 2.1–2.3:
AC-01/03/15/17/18/31; secondary ACs extend coverage without reducing the
mandatory set.

- **P0 — preconditions (per product).** Pin an exact release/commit and
  binary digest and record it with a bundled-licence inventory in the run
  report. Confirm the licence/terms permit the intended trial (per the
  consequences above). Resolve an authorized target in
  `lab/targets.json`; pending or absent targets refuse. No production and
  no real credentials are in scope.
- **P1 — S1 connect and inventory.** Enroll `source` (agent, helper or
  SSH per the product's model). Record host-key handling, the produced
  inventory, whether WordOps objects (sites, vhosts, docroots, site→DB
  mapping, dynamic `wp-config`, the fixture's two drift records) are
  detected, and whether any site PHP executes. REG-01–05, RST-01;
  primary **AC-01**, **AC-03**; secondary AC-02/04/33.
- **P2 — S2 backup and monitoring.** Configure a plan for `site-alpha`;
  run a full capture of files plus database, then a scheduled run and an
  interrupted run. Record completeness labelling, separate assurance
  states, per-site failure isolation and which destinations the licence
  tier allows. BKP-01–08, VER-01/02, UI-02; secondary AC-05–09/13/14/34.
- **P3 — S3 clean-target restore.** Make `source` genuinely unavailable;
  attempt restore to `clean-target`. Record exactly which steps the
  product automates (stack provisioning, vhost, database create/import,
  TLS, DNS) and which stay operator-manual. RST-02/04/05/09; primary
  **AC-15**; secondary AC-16/20/23.
- **P4 — S4 existing-target create/clone/replace.** On `existing-target`
  holding `site-alpha`, `neighbor-beta` and `neighbor-gamma`: create or
  clone, then replace `site-alpha`, injecting one failure each at dump,
  prepare, database import, config and cutover. Record plan/approval
  binding, checkpoint creation and verification, rollback or
  `needs_operator`, and continuous neighbor hash/config/database plus
  write probes. RST-03–10; primary **AC-17**, **AC-18**; secondary
  AC-19/21/22/24/25/35.
- **P5 — S5 suspicious point.** Apply the fixture's safe indicators;
  record finding states, trusted-baseline comparison, quarantine
  labelling and whether production restore of a flagged point is blocked
  by default. SEC-01–03, RST-11; secondary AC-27/28/29.
- **P6 — S6 control-plane loss.** Remove the product's control database
  or dashboard state; reconnect storage plus separately retained keys and
  configuration; attempt a catalog-equivalent rebuild. Record whether
  schedules stay disabled until re-verification and whether orphan or
  incomplete data is excluded. S6, STO-04/05; primary **AC-31**;
  secondary AC-32.

### Current recorded state per product

Nothing is `tested`: no probe has run on any product. `documented` means a
primary source describes the capability or boundary; `unknown` means the
reviewed sources are silent (not that the product lacks the capability).

| Probe | Reaver | Backrest | Duplicati |
|---|---|---|---|
| Licence/API inventory | `documented` — commercial terms; API/MCP paid-only | `documented` — GPL-3.0; gRPC/HTTP gateway | `documented` — MIT with `proprietary/` and third-party carve-outs |
| P1 S1 inventory | `documented` — SSH/manual agent install, WordPress auto-discovery; WordOps-level objects `unknown` | `unknown` | `unknown` |
| P2 S2 backup | `documented` — restic increments, schedules; offsite is a paid-tier feature | `documented` — restic repositories, cron plans, notifications | `documented` — FTP/S3 destinations, schedules, verification options |
| P3 S3 clean restore | `documented` — restore exists, but the new-server guide leaves web/DB stack setup to the operator; WordOps provisioning `unknown` | `unknown` | `documented` — direct restore to a new machine without the original install; site/stack orchestration `unknown` |
| P4 S4 create/clone/replace | `unknown` | `unknown` | `unknown` |
| P5 S5 suspicious point | `unknown` | `unknown` | `unknown` |
| P6 S6 control-plane loss | `unknown` — the dashboard SQLite database is the source of truth; no rebuild-from-storage procedure found | `documented` — import of existing restic repositories (repo level, not a full control-plane catalog) | `documented` — restore from remote files and RecoveryTool without the original install |
| Hands-on trial (any product) | `blocked` — paid-licence authorization, pinned installer, authorized target | `blocked` — pinned release, authorized target | `blocked` — pinned release, authorized target, `proprietary/` touchpoint check |

Totals across the six scenario probes: **8 documented, 10 unknown** across
18 cells; all 3 product trials **blocked** on the prerequisites below;
**0 tested** results.

## Missing trial prerequisites

1. **Release/binary selection.** No version is chosen; every run must pin
   an exact release/commit, a binary digest and a bundled-licence
   inventory. Source snapshots above are observations, not selections.
2. **Authorized disposable targets.** `local-sandbox` is the only
   executable entry in `lab/targets.json` and is not a WordOps
   environment; `wov-g000-containers` (coordinator-run) and
   `wov-g000-vps-pair` remain `authorized=false`.
3. **Real WordPress/WooCommerce fixture** on a pinned disposable WordOps
   stack; the synthetic stand-ins verify protocol mechanics only.
4. **Reaver licence for the suite.** Free covers evaluation/
   non-commercial use of one site with local storage; API, offsite and
   multi-site coverage need a paid plan and registration. No purchase or
   registration is authorized, so the full Reaver trial is `blocked`
   pending a separate authorization decision.
5. **Egress policy for installation.** The lab enforces zero external
   egress, while installers fetch binaries (restic auto-download, the
   Reaver CDN installer, Duplicati runtime). Trials need pre-seeded
   pinned artifacts or an explicit egress allowance.
6. **Integration licence assessments.** Duplicati `proprietary/`
   touchpoints; Backrest GPL obligations for embedding or forking;
   Reaver has no public source, so deeper reuse questions are themselves
   blocked on vendor material.

## Remaining technical unknowns

- WordOps-aware inventory (REG-02/03 objects, drift detection, no site
  PHP execution) for all three products.
- Safe create/clone/replace with neighbor preservation and rollback
  (AC-17/18) for all three.
- Consistency and writer handling (BKP-05/06) for all three.
- WOVault-semantics catalog rebuild after control-plane loss (AC-31):
  documented file- or repository-level recovery does not imply
  plan/identity catalog equivalence.
- Secret handling in logs and API responses. Reaver documents that API
  responses exclude destination keys, restic passwords and agent
  secrets — a vendor claim, untested; AC-33 remains open.
- Exact release artifacts, digests and OS/version matrices for all three.

## Implications for adopt/integrate/build

None yet — this is documentary preparation. The licence/API inventory
feeds the decision record, and the shared protocol defines identical
probes whose outcomes will. OpenSpec tasks 2.1–2.4 remain open, hands-on
G0 tasks are not closed by this document, and ADR 0001 stays proposed.
