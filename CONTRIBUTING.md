# Contributing

The project is currently a specification, not a working backup application.
Please start with the [PRD](docs/PRD.md) and [research](docs/research/landscape.md).

Use issues for requirements, compatibility reports, and proposed changes. Reference
requirement IDs and acceptance scenarios when proposing implementation work.
Keep source-backed observations separate from assumptions and test results.

English is the authoritative language for public documentation, ADRs, research
summaries, OpenSpec artifacts and AgentMarshal change-request contracts, including
acceptance criteria. Write new material and updates in English.

Secondary translations are optional and non-authoritative. Record the source date
or revision when maintaining one, and update it as needed. Preserve requirement IDs,
acceptance-scenario IDs, priorities, commands, paths and machine-readable states.
Do not silently change requirement meaning when translating. This language policy
does not change the product's planned English/Russian UI support.

Use synthetic domains under example.com, example.net, or example.org and
documentation IP addresses. Remove secrets and private customer data from logs.
Do not copy production helper scripts or configurations into this repository
without first generalizing and reviewing them.

Before merging executable code, add checks appropriate to its risk, dependency
license review, and the recovery acceptance tests in the delivery plan. A successful
backup alone is not sufficient validation of a restore implementation.
