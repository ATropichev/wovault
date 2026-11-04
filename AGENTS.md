# Working on WOVault

Read README.md, docs/PRD.md, docs/research/landscape.md and docs/roadmap.md first.
The application does not exist yet. G0 experiments must precede final stack and
engine decisions; docs/decisions/0001-scope-and-engines.md remains proposed.

## Boundaries

- This repository is public. Use synthetic fixtures, example.com domains and
  documentation IPs. Never add credentials, dumps, customer data or raw inventories.
- Production servers require a separate explicit assignment. G0 uses disposable,
  explicitly designated lab targets; local tooling setup does not authorize VPS use.
- Preserve web UI, registry, SSH pull, S3 and FTP/FTPS, integrity/security findings,
  clean-VPS recovery and safe existing-site replacement as stable-release scope.
- Keep transfer, completeness, consistency, integrity, restore-test and security
  results separate. Unknown or unsupported never means passed.

## Tools and evidence

Write public documentation, ADRs, research summaries, OpenSpec artifacts and
AgentMarshal CR contracts/acceptance criteria in English. English documents are
authoritative; secondary translations are optional. Preserve requirement IDs,
priorities, scenario IDs and machine-readable states when translating.

See docs/development.md. Run `scripts/setup-tools` once, then
`export PATH="$PWD/scripts:$PATH"` and `export AGENTMARSHAL_ACTOR=agent-codex`.
Use `agentmarshal` and `openspec` from that PATH; versions are pinned locally.
Run `scripts/check` before submitting changes.

## Task workflow

See docs/agent-workflow.md. The coordinator defines the contract, the implementer
works within its scope, and an independent reviewer judges the committed candidate.
No particular model vendor or agent launcher is required to contribute.

When a harness commits work on your behalf, do not commit, push, switch branches
or rewrite history yourself. Do not hand-edit the journal. A candidate commit is
not acceptance: independent review, confirmed CI and the AgentMarshal gate are
still required.

OpenSpec describes changes; AgentMarshal records scoped contracts and evidence.
For a governed task, open a contract using `agentmarshal open --contract-file ...`,
then read `agentmarshal brief --task CR-...`. Include the specific change documents
and `extensions = ["openspec"]` in schema-2 contracts. Do not hand-edit journal
records. Configuration and extension manifests are configuration, not evidence.

Do not claim gate/CI/independent review passed without actual evidence for the
candidate SHA. An implementer cannot supply their own independent approval.
Do not archive G0 or tick experiment tasks just because planning artifacts validate.
For a public contribution keep contracts, reviews and reports safe for publication.
