# WOVault

An independent, self-hosted backup and recovery control plane for WordOps sites.

**Status: product discovery and specification. No application or installer is implemented yet.**

WOVault is designed to run outside the servers it protects, pull backups over SSH,
store encrypted recovery points in S3-compatible storage or FTP/FTPS, and guide
restoration onto a clean VPS or an existing WordOps server. A server registry,
scheduled integrity checks, isolated restore tests, and evidence-based security
findings are part of the proposed product.

## Start here

- [PRD — product requirements (Russian)](docs/PRD.md)
- [Research — alternatives and build-versus-integrate decision](docs/research/landscape.md)
- [Research sources and methodology](docs/research/sources.md)
- [Architecture proposal](docs/architecture.md)
- [Threat model and privilege boundaries](docs/threat-model.md)
- [Delivery plan and acceptance scenarios](docs/roadmap.md)
- [ADR 0001 — product scope and backup engines](docs/decisions/0001-scope-and-engines.md)
- [Illustrative recovery manifest](examples/recovery-manifest.json)

The specifications are dated **2026-11-04**. Requirements describe intended
behavior; they are not claims about available software. Research is based on
public primary sources, not a hands-on certification of competing products.

## Intended workflow

1. Register a WordOps server and verify its SSH host key.
2. Inventory the environment and enroll a restricted backup account.
3. Select sites, storage, schedule, retention, and consistency policy.
4. Track backup freshness, integrity, restore-test results, and security findings.
5. Select a retained recovery point and a target VPS.
6. Review the target inventory and restore plan, then create or replace a site.

Backups, integrity, application consistency, and signs of compromise have separate
statuses. A completed backup is never automatically described as malware-free.

## Scope and deployment

The first supported deployment is a dedicated Linux VM/VPS with persistent
workers and staging storage. Ordinary PHP-only shared hosting is not a deployment
target. The initial product is single-organization, with administrator, operator,
and viewer roles; hosted multi-tenant SaaS is outside the first release.

There is no affiliation with or endorsement by the WordOps project. WordOps
retains its own name and licensing. The name WOVault is provisional: a repository
name search was performed, but no trademark or domain clearance is claimed.

## Public development

This repository intentionally contains synthetic examples only. Never submit
production dumps, customer information, SSH keys, passwords, or private server
inventories. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

Original material is provided under the [MIT license](LICENSE). Third-party tools
retain their respective licenses; the project does not copy competitor code.
