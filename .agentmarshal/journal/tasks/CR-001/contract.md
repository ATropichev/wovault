+++
schema = 2
id = "CR-001"
title = "G0-00: reproducible lab and evidence protocol"
scope = ["lab/", "docs/research/"]
acceptance = ["Explicit disposable-target allowlist and cleanup plan exist; no production access", "Pinned synthetic fixtures and repeatable input manifests exist", "Machine-readable evidence rejects missing required fields and distinguishes unknown from tested-pass", "Isolation, reset and secret-canary checks have actual run evidence"]
documents = ["docs/PRD.md", "docs/implementation-plan.md", "docs/research/experiment-template.md", "openspec/changes/validate-g0-feasibility/"]
extensions = ["openspec"]
+++

# G0-00: lab and evidence protocol

Implement only group 1 of validate-g0-feasibility/tasks.md. Other G0 groups need
separate contracts. This task is opened for future execution, not already done.
Lab target authorization and resource limits must be established before remote
execution. Use synthetic fixtures only. No production operations are authorized.
Do not finalize architecture, engines or supported versions from setup alone.
