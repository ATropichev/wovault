# Coordinator review after the first repair

Candidate: cae8facfff41ac9065569d1fe81b082b94e5e76b.
Verdict: changes_required.

This is the coordinator's actual review, based on source inspection, coordinator
probes and the independent Astra high audit. It is not a fresh configured Sol
reviewer session. Fresh independent review of the final publication SHA remains
mandatory. No CI success or owner acceptance is claimed.

F1 — security: fixture generation accepts arbitrary --out and deletes existing
fixture directories there; run_checks accepts arbitrary --workdir before ownership
validation. The auditor reproduced both with mutations mocked. Validate every
mutating destination, including symlinked ancestors, before creation/deletion/copy.
Keep evidence publication separately scoped. Add persistent regression coverage.

F2 — security: cleanup --containers bypasses the executable target allowlist and
can remove prefix-matching names while the target is pending/unauthorized.
Require activation, the approved local daemon and concrete owned resources.
Pending profiles must remain blocked without contacting arbitrary Docker contexts.

F3 — security: the inner isolation command binds the whole host root read-only,
inherits environment and lacks PID separation. Narrow mounts, clear environment,
isolate processes, and test parent-file, environment and process confidentiality.
No stronger escape was demonstrated. Never weaken confinement to make tests pass.

F4 — contract-mismatch: tested verdicts can contain an empty command reference or
nonexistent file with a syntactically valid digest. Require meaningful evidence
content and verify artifact existence/hashes at acceptance/publication. Remove
claims that structural validation makes execution evidence non-forgeable. Test
missing/stale/tampered artifacts.

F5 — claim-accuracy: all six assurance dimensions are missing from reports; one
passing fixture scenario permits every dimension to be passed. Emit explicit
not_checked in this scaffold. Promotion needs relevant dimension-specific evidence.

F6 — security: scan reports clean for missing paths and skips unreadable/invalid
UTF-8 files. Search bytes, report incomplete coverage as non-success, and test
missing/unreadable/binary input with and without canary tokens.

F7 — correctness: cleanup only runs in the isolation group. Standalone groups and
exceptions may leave resources without cleanup evidence. Finalize each run on
success/failure, retain leftovers and intentional --no-cleanup explicitly.

F8 — correctness: the coordinator rerun emitted two tested-fail outcomes while
run_checks exited 0 because it only checked report validity. Fail the command for
tested-fail outcomes; distinguish valid reports from successful experiments.
The observed namespace failures were the outer environment denying NETLINK_ROUTE
before the payload ran, not demonstrated egress. Classify unavailable setup honestly.

Preserve unique run evidence; distinguish declared from enforced resource budgets.
CI integration requiring paths outside this scope needs a follow-up contract.
Earlier fixes and four reports' hashes were confirmed, but these new blockers remain.
No actual container removal, cloud or production operation occurred in this review.
