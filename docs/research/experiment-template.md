# G0-XX — experiment name

Status: planned. This is a template, not a report of a completed test.

## Hypothesis and criterion

- Requirement IDs / AC IDs:
- Claim under test and expected outcome:
- Failure condition / condition for switching to an alternative:
- Product under test, release/commit, license source and verification date:

## Reproduction

- UTC run time and run ID:
- Fixture generator/commit and input-artifact digests:
- OS/WordOps/PHP/database/client/storage versions and topology:
- Authorized disposable targets and reset/cleanup procedure (no credentials;
  reset/cleanup refuse anything outside the explicit allowlist, including
  through symlinks, and never destroy the baseline they restore from):
- Synthetic addresses, resource limits and network policy:
- Exact commands, preconditions and action order:

## Observations

| Scenario / fault point | Expected | Actual / exit code | Evidence digest | Verdict |
|---|---|---|---|---|
| Complete after execution | — | Not run | — | planned |

Allowed verdicts: planned, documented, tested-pass, tested-fail, blocked, unknown.
For documented, provide a primary source; for blocked, the obstacle and next action.
For tested results, provide reproducible commands and safe evidence artifacts.
A tested verdict requires an actual run record and meaningful evidence content —
not an empty command reference or a digest pointing at a missing or tampered
file. When setup fails before the payload or measurement starts (e.g. a
namespace could not be created), record blocked with the setup error as the
evidence: a refusal to run is not a tested-fail, and a structurally valid
report is not a successful run — the check command itself must fail on
tested-fail. Coverage-limited probes (missing or unreadable inputs) are
non-success outcomes, never clean results.

## Measurements and decision

- Data size, wall time, pause, RTO, peak staging/checkpoint, CPU/RAM, bytes/requests:
- Separate completeness, consistency, integrity, restore-test and security outcomes:
- Neighboring-site state and cleanup confirmation (including failed removals —
  a cleanup attempt that did not succeed is reported, not confirmed; every run
  finalizes with a cleanup record, so an intentional no-cleanup pass is itself
  an explicit leftover, not a silent skip):
- Limitations, residual risks and what was not tested:
- Implications for adopt/integrate/build; required follow-up:
- Check for credentials/restricted information before public inclusion; file
  and log evidence entries carry a sha256 digest, and all recorded paths are
  repository-relative so no workstation-private paths enter public artifacts:
