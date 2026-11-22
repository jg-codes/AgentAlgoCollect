# Sanitize evidence before publishing

1. Record the machine with `python tools/stamp.py` (CPU model, cores, memory, operating system
   family, Python version). Use `--coarse` if even the CPU model should stay private. Do not paste
   system reports.
2. In logs and result files, replace absolute paths by paths relative to the entry.
3. Remove host names, user names, addresses, serial numbers, e-mail addresses, keys and tokens.
   Keep every measured value unchanged; if a file cannot be cleaned without touching results,
   regenerate it instead of editing it.
4. Run `python tools/scan_sensitive.py`. Fix every finding. Add an exception to `.sensitive-allow`
   only with a reason, and never for real personal data or secrets.
5. Note in the entry README if evidence files were regenerated or cleaned.
