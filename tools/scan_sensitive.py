"""Block secrets, personal data and machine-identifying details before they are published.

Usage: python tools/scan_sensitive.py            # scan all tracked files
       python tools/scan_sensitive.py FILE ...   # scan given files (used by the commit hook)

Exit code 1 if anything is found. A finding is never removed automatically: evidence files must not
be rewritten silently. Fix the file, or add a justified exception to `.sensitive-allow`
(one `path-glob :: rule` per line).
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RULES: dict[str, re.Pattern[str]] = {
    # secrets
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "github-token": re.compile(
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b"
    ),
    "api-key": re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|hf_[A-Za-z0-9]{30,})\b"
    ),
    "assigned-secret": re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\b"
        r"""\s*[:=]\s*["']?[A-Za-z0-9+/_\-]{12,}"""
    ),
    # personal data
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<![\w.])\+\d{1,3}[ -]?\(?\d{2,4}\)?[ -]?\d{3,4}[ -]?\d{3,5}(?!\w)"),
    # machine and user identification
    "home-path": re.compile(
        r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)(?!runner\b|user\b|USER\b|<)[A-Za-z0-9._-]+"
    ),
    "ip-address": re.compile(r"\b(?!0\.0\.0\.0|127\.0\.0\.1)(?:\d{1,3}\.){3}\d{1,3}\b"),
    "mac-address": re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b"),
    "machine-identity": re.compile(
        r"(?i)\b(?:serial[ _-]?number|hardware[ _-]?uuid|machine[ _-]?uuid|"
        r"""hostname|computer[ _-]?name|host[ _-]?name)\b["']?\s*[:=]\s*["']?[\w.-]{3,}"""
    ),
}
# Values that identify nobody.
SAFE_EMAIL = re.compile(
    r"(?i)(?:noreply|no-reply)@|@users\.noreply\.github\.com|@example\.(?:com|org)"
)
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xz", ".gz", ".zip")
SKIP_FILES = ("LICENSE",)


def load_allow() -> list[tuple[str, str]]:
    path = ROOT / ".sensitive-allow"
    out = []
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if "::" in line:
                glob, rule = (x.strip() for x in line.split("::", 1))
                out.append((glob, rule))
    return out


def scan_text(rel: str, text: str, allow: list[tuple[str, str]]) -> list[str]:
    findings = []
    for name, pattern in RULES.items():
        if any(fnmatch.fnmatch(rel, g) and r in (name, "*") for g, r in allow):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in pattern.finditer(line):
                if name == "email" and SAFE_EMAIL.search(m.group(0)):
                    continue
                if name == "ip-address" and not all(int(x) <= 255 for x in m.group(0).split(".")):
                    continue
                findings.append(f"{rel}:{n}: {name}: {m.group(0)[:40]}")
    return findings


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


def main(args: list[str]) -> int:
    files = args or tracked_files()
    allow = load_allow()
    findings: list[str] = []
    for rel in files:
        path = ROOT / rel
        if not path.is_file() or rel.endswith(SKIP_SUFFIXES) or Path(rel).name in SKIP_FILES:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        findings += scan_text(rel, text, allow)
    for f in findings:
        print(f)
    if findings:
        print(
            f"\n{len(findings)} finding(s). Remove them, or add a justified line to .sensitive-allow."
        )
        return 1
    print(f"no sensitive data found in {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
