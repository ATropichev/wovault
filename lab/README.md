# G0 synthetic lab

Disposable, synthetic-only lab for the G0 feasibility experiments in
[docs/implementation-plan.md](../docs/implementation-plan.md). This is not a
WOVault deployment and installs no WordOps/WordPress/Nginx/PHP/database
software: it provides reproducible inputs, an evidence format and the
protocol checks every later experiment relies on.

Scope of authorization: the owner approved autonomous G0 work starting with a
local-only synthetic lab (task CR-001). No production access, cloud APIs, paid
trials or Selectel resources are authorized. Remote execution needs a separate
explicit assignment; container execution is owned by the coordinator.

## Layout

| Path | Contents |
|---|---|
| `targets.json` | Executable target allowlist: only entries under `targets` may be executed against; `pending_targets` documents planned coordinator-run profiles and stays non-executable |
| `resources.json` | Task-owned resource allowlist: reset/cleanup refuse everything outside it |
| `topology.md` | Lab roles, network policy, resource budget and the cleanup plan |
| `fixtures/pins.json` | Pinned generator inputs: seed, simulated versions, canary tokens, fixture list |
| `fixtures/generate.py` | Deterministic fixture generator (stdlib only) |
| `fixtures/expected/` | Expected manifests the generated trees must match |
| `evidence/report.schema.json` | Published contract for G0 evidence reports |
| `evidence/validate.py` | Canonical stdlib validator for that schema |
| `evidence/examples/` | Valid and rejected example reports (`valid-*`/`err-*`) |
| `evidence/runs/` | Retained, sanitized run reports and artifacts |
| `tools/labctl.py` | Allowlist verify/resolve, reset, cleanup, canary scan/redact |
| `tools/run_checks.py` | Check orchestrator; emits schema-valid reports |
| `tools/payloads/` | Payloads executed inside isolation namespaces |

Runtime scratch (generated fixture trees, namespaces, workspaces) lives under
`lab-output/` at the repository root and is gitignored; retained evidence is
small sanitized files under `lab/evidence/runs/`. Every mutating destination —
`generate.py --out`, `run_checks.py --workdir`, `labctl.py redact --out` — is
resolved and must stay inside a task-owned prefix, including through
symlinked ancestors; `--publish` is scoped separately and must stay inside
`lab/evidence/runs/`.

Each invocation creates a new scratch workspace. An existing `--workdir` is
refused intact, including any stale symlinks; use a new path for another run.

## Requirements

Python ≥3.12, standard library only. The isolation check uses `bwrap`
(`--unshare-all`: user, mount, network, PID, UTS and IPC namespaces, a
read-only root skeleton, a cleared environment and one writable docroot) —
`unshare` is probed for context. No Docker daemon, no network access and no
third-party packages are needed for the local profile. The
`canonical-schema-agreement` scenario additionally cross-checks
`evidence/validate.py` against the published JSON Schema with the
`jsonschema` package when it is importable; without it that single scenario
is `blocked`, never skipped.

## Usage

```sh
# verify the executable allowlist (task 1.1)
python3 lab/tools/labctl.py verify-allowlist

# generate fixtures and compare against the pinned manifests (task 1.2)
python3 lab/fixtures/generate.py generate          # -> lab-output/fixtures/
python3 lab/fixtures/generate.py --check           # compare vs expected/

# validate an evidence report (task 1.3); --no-artifact-check limits it to
# structure only — publication requires the default artifact verification
python3 lab/evidence/validate.py REPORT.json --summary
python3 lab/evidence/validate.py --selftest

# publication ownership, error-report sanitization and malformed-input regressions
python3 -B -m unittest discover -s lab/tests -v

# run all protocol checks (tasks 1.1–1.4); reports land in lab/evidence/runs/
python3 lab/tools/run_checks.py all

# reset / cleanup operate only inside lab-output/ and refuse anything else,
# including paths that escape through symlinks; reset also refuses
# scope/baseline pairs where one contains the other
python3 lab/tools/labctl.py reset --scope lab-output/x --baseline lab-output/base
python3 lab/tools/labctl.py cleanup --apply --path lab-output/runs/<ts>
python3 lab/tools/labctl.py cleanup --containers    # coordinator-run profile
```

Every run writes a `g0-evidence/1` report: scenario-level `expected`/`actual`/
`verdict`, evidence digests, UTC run times, executor environment, all six
assurance dimensions (explicit `not_checked` in this scaffold) and a cleanup
block. `planned`, `documented`, `blocked` and `unknown` are valid outcomes
but never count as passes; only `tested-pass` does, and it requires a real
run record (`exit_code`, `ran_at`, `duration_ms`) plus evidence. Evidence
entries must carry content — a `command`/`stdout` entry needs a non-empty
note or digested path, and every recorded path must exist and match its
sha256 at validation time.

`run_checks.py` finalizes each group with a cleanup record on success,
failure or exception (`--no-cleanup` is recorded explicitly), and exits
non-zero when any report is invalid, any scenario is `tested-fail` or a
group crashes: a valid report is not the same as a successful experiment.
A scenario whose payload never ran (namespace/setup failure) is `blocked`,
not `tested-fail` — setup refusal is not a demonstrated isolation result.

## Canaries

`fixtures/pins.json` defines synthetic `WOVAULT-CANARY-*` tokens. They may
appear only in fixture definitions and generated fixture trees — never in
`lab/evidence/`, reports, logs or public artifacts. `labctl.py scan`
byte-searches them (exit 1 on any hit, covering binary and non-UTF-8 files;
exit 2 when coverage is incomplete — a missing path or unreadable file is
never a clean scan). `labctl.py redact` replaces values with
`REDACTED:<id>` byte-exact for sanitization checks.

## Coordinator-run profile

The local environment has no Docker socket, so container isolation evidence is
`blocked` in the local reports — not skipped silently. While the
`wov-g000-containers` entry stays in `pending_targets`, `labctl.py cleanup
--containers` refuses without contacting any Docker daemon, whatever
`DOCKER_HOST`/`DOCKER_CONTEXT` points at. Activation means the coordinator
moves the entry into `targets` with `authorized=true`; container operations
then require the approved local daemon endpoint (unset or local
`DOCKER_HOST`, default context) and act only on concrete `wov-g000-*` names.

When the coordinator runs the container profile it MUST produce equivalent
schema-valid reports. Required coordinator steps (all names are covered by
`resources.json`; any other container is refused):

```sh
docker network create --internal wov-g000-net            # no egress
docker run --name wov-g000-<role> --network wov-g000-net --read-only <image>
# run the same payloads/checks per role
python3 lab/tools/labctl.py cleanup --containers --apply  # removes wov-g000-* only
```

Container image tags/digests are pinned and recorded by that coordinator run's
own evidence report — they are intentionally absent here, since this task has
not executed or validated any image. Remote-VPS profiles additionally require
the named-target authorization described in `targets.json`.

## Adding a G0 experiment report

1. Resolve a target: `labctl.py resolve --target <name>` (refuses non-allowlisted).
2. Run the experiment on disposable resources only; keep artifacts small.
3. Write a report following `evidence/report.schema.json` and
   [docs/research/experiment-template.md](../docs/research/experiment-template.md).
4. `python3 lab/evidence/validate.py your-report.json` — it must pass.
5. `python3 lab/tools/labctl.py scan --paths lab/evidence` — must stay clean.
6. `python3 lab/tools/labctl.py cleanup --apply` — remove the run workspace.
