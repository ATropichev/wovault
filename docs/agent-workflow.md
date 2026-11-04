# Task contracts, review and evidence

WOVault uses OpenSpec to describe intended changes and AgentMarshal to record
contracts, execution evidence and independent reviews. Contributors can use
ordinary Git and the pinned CLIs; no particular agent, model provider or launcher
is required. Human and automated work follow the same acceptance criteria.

## Prepare the repository

Install tools and run public checks as described in [Development](development.md):

```sh
scripts/setup-tools
scripts/agentmarshal doctor
scripts/check
```

An agent must declare `AGENTMARSHAL_ACTOR` before writing records. Keep contributor
and reviewer identities distinct and truthful. Actor IDs are declarations, not
proof of identity. The actor table supports interpretation of recorded evidence;
it does not require contributors to use those actors or model providers.

The current checks validate the journal, OpenSpec, the example recovery manifest
and diff whitespace. They do not establish that backups or restoration work.
Tests appropriate to executable product components will be added with those components.

## Work on a bounded change

1. Identify PRD requirements and acceptance scenarios. For the current phase,
   use the G0 order in [Implementation plan](implementation-plan.md).
2. Prepare the OpenSpec change and a small English CR contract with scope,
   acceptance criteria and document references. Use the contract example in
   [Development](development.md); open it through `agentmarshal open`.
3. Commit the contract before implementation. Read the assigned brief:
   `scripts/agentmarshal brief --task CR-001` (use the actual assigned ID).
4. Implement on a task branch or worktree. Preserve unrelated work, stay within
   scope and use synthetic data. Amend the contract through the CLI when an
   authorized scope change is necessary; do not rewrite journal files by hand.
5. Run the public checks and the task's actual acceptance tests. Record what ran,
   including failures and unknowns. Commit the candidate for independent review.

`CR-001` currently covers G0-00 only. Infrastructure preparation, tooling validation
and a completed proposal do not complete its experiments. Production access and
paid lab provisioning need their own explicit assignment.

## Independent review and merge

The reviewer checks a specific candidate SHA against its contract, scope, tests
and applicable threat model. The implementer cannot approve their own work.
Record an actual external review through `agentmarshal submit-review`; use
`scripts/agentmarshal submit-review --help` for the required structured fields.
An automated reviewer may instead use the standard `agentmarshal review` adapter
interface. Neither route permits inventing a human decision or successful checks.

Before merging, run `agentmarshal gate` against the candidate and its comparison
base, with confirmed CI attestation for the relevant SHA. The command's
`--attestation ci-required` mode depends on genuinely required provider checks;
it does not configure GitHub protection. See `scripts/agentmarshal gate --help`.

Changing the candidate after review requires another review of the new SHA.
Squash/rebase changes SHAs and must be accounted for by the integration procedure.
After a successful gate and integration, record completion through the CLI and
preserve the reviewed candidate and comparison-base references. Complete and archive
an OpenSpec change only after all of its required work and acceptance are finished.

The [GitHub protection policy](github-governance.md) requires specification checks,
the CI scope/journal gate and a separate full-gate status. Its public procedure
applies equally to manual work and automation; there are no unpublished acceptance
conditions or required commercial model subscriptions.

## Public evidence

Contracts, applicable specifications, review records and test summaries must be
safe for publication and sufficient to assess the claimed result. Never commit
credentials, customer data, raw production inventories or unredacted transcripts.
Only actual evidence can close an experiment; `unknown` does not mean `passed`.
