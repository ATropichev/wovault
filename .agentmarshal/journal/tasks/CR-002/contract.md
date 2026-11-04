+++
schema = 2
id = "CR-002"
title = "Enforce local lab regressions in required CI and record G0-00 progress"
scope = ["scripts/check", "docs/development.md", "docs/github-governance.md", "openspec/changes/validate-g0-feasibility/tasks.md"]
acceptance = ["The required specification check runs existing lab regression tests, canonical report examples and pinned fixture verification and propagates command failures", "Only completed local G0-00 tasks are marked complete using CR-001 evidence; later G0 tasks remain open", "Public documentation describes actual CI coverage and labels an unavailable optional JSON Schema comparison as skipped rather than passed", "Public checks and independent review validate the committed candidate without private driver dependencies"]
documents = ["docs/development.md", "docs/research/g0-00-lab-and-evidence-protocol.md", "openspec/changes/validate-g0-feasibility/tasks.md"]
extensions = ["openspec"]
+++

# Local regression enforcement after CR-001

Integrate the existing dependency-free laboratory checks into scripts/check,
which is already executed by the required specifications job. The full mutating
namespace experiment suite remains a separately evidenced local profile.
Record completed G0-00 progress against the merged CR-001 implementation and
journal. Subsequent product trials, WordOps qualification and engine decisions
remain in their existing G0 tasks. Public checks stay independent of private drivers.
