# Security

This repository holds research code and benchmark drivers. Run it in an isolated environment, as you
would any code from the internet.

If you find a vulnerability, or an entry whose scripts do something other than what the entry
describes, report it privately through GitHub's "Report a vulnerability" on the Security tab, or by
private message to @jg-codes. Please do not open a public issue for it.

Every pull request is scanned for secrets, personal data and machine identifiers
(`tools/scan_sensitive.py`). If you find such data in the repository or its history, report it
privately as above so it can be removed.

Pull requests are reviewed for scripts that download or execute unexpected code. Entries must fetch
external files from their original public source and record checksums.
