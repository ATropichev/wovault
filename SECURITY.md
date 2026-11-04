# Security policy

There is no runnable release and no supported production version yet.

Do not put credentials, backup archives, personal information, exploit payloads
against real hosts, or unredacted inventories into public issues.

Use GitHub's **Report a vulnerability** / private vulnerability reporting for this
repository once enabled. If it is unavailable, open a public issue containing only
a request for a private reporting channel, without sensitive details.

The proposed system has privileged recovery capabilities and reads private site
data. See the [threat model](docs/threat-model.md) for the intended boundaries.
Its checks detect selected indicators; they do not prove that a source host or a
backup is free from compromise.
