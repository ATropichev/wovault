# GitHub merge protection

The protected branch is `main`. All changes after the initial tooling bootstrap
must arrive through pull requests. Force pushes and deletion are forbidden,
including for administrators. Required conversations must be resolved and the
candidate must be up to date with `main`. Only merge commits are enabled, so the
reviewed candidate remains identifiable in the resulting history.

## Required checks

| Context | Publisher | Meaning |
| --- | --- | --- |
| `specifications` | GitHub Actions | Journal, OpenSpec, manifest, lab regressions/report examples/pinned fixtures and whitespace validation |
| `agentmarshal-gate` | GitHub Actions | Contract, scope, append-only journal and lifecycle checks on the exact PR head |
| `agentmarshal-review` | Trusted maintainer | Full AgentMarshal gate, with actual exact-SHA CI and required independent review evidence |

The first two checks are bound to the GitHub Actions app. The third is an external
commit status: an absent, pending or failed status blocks merging. Repository-write
credentials can publish statuses and are a trust boundary, not proof of independent
review by themselves. These credentials must never be supplied to candidate code,
fork workflows or an implementing agent. Maintainer access is trusted; this design
does not authenticate model identities cryptographically.

The checked-in desired protection settings are in
[branch-protection.json](../.github/branch-protection.json). They take effect only
after being applied to GitHub; committing the file alone does not configure the
server. Public workflow tokens have read-only contents access and no permission
to publish the external approval status.

## What the CI gate does and does not check

The PR branch must contain exactly one `CR-<number>` identifier. CI checks the
exact PR head and event base using the released AgentMarshal 0.6.0 installed
outside the candidate's source tree. No private launcher is needed in CI.

AgentMarshal's GitHub template uses `--without-review`: a head cannot already
contain a review record naming itself. That check is necessary but insufficient
for merging an implementation. The separate `agentmarshal-review` status closes
this workflow gap: the maintainer evaluates the full gate with the actual local
review record before publishing success. Journal-only operations use the full
gate's normal opening/completion rules; they do not fabricate an implementation review.

## Publishing a genuine full-gate result

This is a maintainer operation, available through standard Git, AgentMarshal and
GitHub APIs. No specific model or commercial agent subscription is required:

1. Resolve the open PR's current head/base SHA and task ID; ensure the local
   candidate matches and contains the current base. Do not use a stale branch.
2. Obtain an independent review of that candidate and record it through the CLI.
   For implementation tasks, changing the code requires a review of the new SHA.
3. Confirm that both named Actions checks actually succeeded on that exact head.
   Missing, skipped, neutral, pending or failed checks do not count as success.
4. Run `agentmarshal gate --task CR-... --commit <head> --base <base>
   --pipeline-sha <head>` with no `--without-review` flag. Set the attestation only
   after step 3. Inspect and resolve every refusal.
5. Recheck the PR's head and base, then publish `agentmarshal-review=success`
   on that head using the GitHub commit-status API. Link the PR as the status target.
   The status records a genuine gate result; it is never a substitute for review.
6. Merge the PR through GitHub after all three required checks pass. Record the
   completion/evidence transaction separately, preserving the pre-merge base and
   reviewed candidate. Retain public-safe review evidence in the journal.

Native GitHub approval count is zero because independent review is enforced by
the full-gate status, not by requiring a second GitHub account. This does not
permit self-review. An additional human GitHub approval may be requested as needed.
There is no automatic merge or merge queue. A merge queue needs a separately
designed `merge_group` validation path; skipped gate jobs must never satisfy it.

References: [AgentMarshal GitHub enforcement](https://github.com/agentmarshal/agentmarshal/blob/v0.6.0/docs/github-enforcement.md),
[GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
[GitHub commit statuses](https://docs.github.com/en/rest/commits/statuses).
