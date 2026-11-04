# Upstream outbox

Findings about **AgentMarshal itself** go here — one file per finding — and are
sent upstream as a batch.

This outbox is **not journal evidence**. Stage journal evidence one task
at a time — `git add .agentmarshal/journal/tasks/<task-id>` — so records
of other tasks in flight never ride in a task's transaction. If staging
`.agentmarshal` itself, exclude this outbox:
`git add .agentmarshal ':(exclude).agentmarshal/upstream/**'`. The
quotes are part of the command — the parentheses are shell metacharacters.

An adopter on a pinned release never patches the tool locally, so everything
noticed about it has exactly one addressee. Without a place to put it, a finding
settles in a chat log or a commit message and never arrives.

## What belongs here

A finding, not a bug title: what was run, what happened, how often, and what the
workaround cost. Measurements are the evidence — counts, ratios, timings — and
they are what upstream quotes.

## Before sending

**Sanitize at source.** Upstream is public and cannot un-publish. Remove
anything specific to this repository or its clients: names, hostnames, internal
paths, task numbers, excerpts of your own code. Send the finding, not the
context it was found in.

The original stays with you. Upstream publishes a digest of each proposal with a
stated disposition, under a pseudonym for the reporter.

See the upstream project's CONTRIBUTING for the language convention and how to
send a batch.

## After sending

Since the batch of 2026-09-16, each published digest carries a `Source:` line —
the sha256 of the file you sent, as sent, in full and in lowercase hex. Hash
the outbox file you sent — `sha256sum` — and search through the files under
`docs/proposals/` — the upstream repository's directory of published digests —
https://github.com/agentmarshal/agentmarshal/tree/master/docs/proposals — for
the result: the entry whose `Source:` line matches is yours, whatever upstream
numbered or titled it. The index `docs/proposals/README.md` lists them, and its
section "Tracking what happened to yours" describes the rest of the protocol.
