# Contributing

The project is currently a specification, not a working backup application.
Please start with the [PRD](docs/PRD.md) and [research](docs/research/landscape.md).

Use issues for requirements, compatibility reports, and proposed changes. Reference
requirement IDs and acceptance scenarios when proposing implementation work.
Keep source-backed observations separate from assumptions and test results.

Documentation is initially in Russian with an English entry point. English
translations and corrections are welcome. Do not change requirement meaning
silently when translating.

Use synthetic domains under example.com, example.net, or example.org and
documentation IP addresses. Remove secrets and private customer data from logs.
Do not copy production helper scripts or configurations into this repository
without first generalizing and reviewing them.

Before merging executable code, add checks appropriate to its risk, dependency
license review, and the recovery acceptance tests in the delivery plan. A successful
backup alone is not sufficient validation of a restore implementation.
