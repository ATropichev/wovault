# G0 lab topology, network policy and cleanup plan

Date: 2026-11-04 · Task: CR-001 (G0-00). This document records the authorized
disposable lab, its budget and how it is torn down. Nothing here authorizes
production access or cloud resources; remote execution needs a separate explicit
assignment. Machine-readable rules live in [targets.json](targets.json) and
[resources.json](resources.json); `lab/tools/labctl.py` enforces them.

## Roles

| Role | Purpose | Documentation address (identifier only, never contacted) |
|---|---|---|
| `source` | WordOps source server stand-in; hosts synthetic sites | 192.0.2.10 |
| `clean-target` | Empty restore target | 192.0.2.20 |
| `existing-target` | Restore site plus two neighbor sites | 192.0.2.30 |
| `control` | Control-plane stand-in; runs checks, staging, evidence | 198.51.100.10 |
| `storage-s3` | S3-compatible endpoint stand-in | 198.51.100.20 |
| `storage-ftp` | FTP/FTPS endpoint stand-in | 198.51.100.30 |

Addresses come from RFC 5737 documentation ranges and exist only as synthetic
identifiers in fixtures. No lab step dials them; isolation checks must prove
that such dials fail.

## Execution profiles

1. **local-namespace** (authorized, executed locally). Roles are directories in
   `lab-output/`; the isolation boundary is a `bwrap --unshare-all` sandbox
   (user, mount, network, PID, UTS and IPC namespaces) with a read-only root
   skeleton, a cleared environment and a single writable docroot. This is the
   only profile CR-001 runs. It provides real namespace evidence, not a real
   WordOps/VPS environment.
2. **container-set** (defined, not authorized for this task). Roles map to
   containers named `wov-g000-<role>` on an isolated bridge. Execution is owned
   by the coordinator; this environment has no Docker socket. Required
   coordinator commands are listed in [README.md](README.md#coordinator-run-profile).
3. **remote-vps** (future). Disposable VPS pairs require named addresses, budget
   and cleanup approval in a separate assignment.

## Network policy

- No external egress from any lab runtime. Isolation checks run payloads with
  `--unshare-net` and must observe connect attempts to documentation-range
  addresses fail.
- No host listeners reachable from outside. Checks may not weaken host firewall
  or DNS.
- Provisioning downloads, when later authorized, happen in a separate phase on
  the `control` role; restored-runtime roles never gain egress (design decision 3
  in the OpenSpec change).

## Resource budget

Per [targets.json](targets.json): ≤4 concurrent targets, ≤2 GiB disk and
≤2 GiB RAM per target, ≤64 MiB per fixture, ≤300 s per check. Small datasets are
deliberate: G0-00 validates the protocol, not capacity. The 50 GiB/5 GiB,
100-site profile is a later measurement.

## Cleanup plan

Ownership boundary: only paths under `lab-output/` and containers named
`wov-g000-*` are task-owned (`lab/resources.json`). Everything else — tracked
files, other checkouts, unrelated containers — is refused by `labctl.py`.
Ownership is decided on the fully resolved path compared against the lexical
owned prefixes, so a symlinked `lab-output/` or a symlink inside it cannot
make an outside directory count as task-owned.

- `labctl.py reset --scope <dir> --baseline <dir>` restores an owned working
  copy to its baseline and removes strays; refuses non-owned paths and any
  scope/baseline pair where one contains the other.
- `labctl.py cleanup --apply` deletes owned run workspaces after retained
  evidence (digests, sanitized logs) has been copied into `lab/evidence/runs/`.
- `labctl.py cleanup --apply --containers` additionally removes `wov-g000-*`
  containers; coordinator-run only and gated on an *activated* container-set
  target plus the approved local Docker endpoint (unset or local
  `DOCKER_HOST`, default context) — while the target is pending it refuses
  without daemon contact. A removal that fails is reported as a leftover
  with `verified=false`; cleanup is never confirmed on a failed removal.
- Every check run finalizes with a cleanup record — on success, failure or
  harness exception — so unrecorded leftovers cannot accumulate. An
  intentional `--no-cleanup` keeps the workspace and records it as an
  explicit leftover rather than a silently skipped step.
- A lost baseline means reset, never blind retry. Cleanup leaves a
  machine-readable result that becomes part of the run report (`cleanup` block).

## Non-goals

The lab does not install WordOps, WordPress, Nginx, PHP or a database for real.
Fixtures are synthetic stand-ins; pinning their content does not pin or validate
upstream software. No combination may be declared supported from this lab alone.
