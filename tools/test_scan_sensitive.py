"""The scanner must catch what it claims to catch and leave ordinary text alone."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan_sensitive as scan  # noqa: E402
import stamp  # noqa: E402

BAD = {
    "private-key": "-----BEGIN OPENSSH PRIVATE KEY-----",
    "github-token": "ghp_" + "a" * 36,
    "api-key": "sk-" + "b" * 30,
    "assigned-secret": 'password = "correcthorsebattery"',
    "email": "contact: jane.doe@university.edu",
    "phone": "call +49 30 1234 5678",
    "home-path": "/Users/janedoe/projects/run.log",
    "ip-address": "server 192.168.178.20 answered",
    "mac-address": "a4:83:e7:12:9f:0b",
    "machine-identity": 'hostname: "janes-macbook-pro"',
}


@pytest.mark.parametrize("rule", sorted(BAD))
def test_rule_fires(rule):
    findings = scan.scan_text("x.txt", BAD[rule], [])
    assert any(f": {rule}: " in f for f in findings), findings


@pytest.mark.parametrize(
    "text",
    [
        "Solved 22/22 within 2.01 s on a 2-core VM with 8 GB RAM.",
        "Co-authored by someone <noreply@example.com>",
        "53511569+user@users.noreply.github.com",
        "version 9.15.6755 of the solver",
        "see https://doi.org/10.1609/aaai.v34i02.5508",
        "/home/runner/work/repo",
        'machine_id = "vm"',
    ],
)
def test_ordinary_text_passes(text):
    assert scan.scan_text("x.txt", text, []) == []


def test_allow_list_is_per_path_and_rule():
    allow = [("docs/*.md", "email")]
    assert scan.scan_text("docs/a.md", BAD["email"], allow) == []
    assert scan.scan_text("src/a.md", BAD["email"], allow)
    assert scan.scan_text("docs/a.md", BAD["phone"], allow)


def test_repository_is_clean():
    assert scan.main([]) == 0


def test_stamp_holds_no_identity():
    s = stamp.stamp()
    assert set(s) == {"cpu", "cores", "memory_gb", "os", "python"}
    import getpass
    import socket

    blob = " ".join(str(v) for v in s.values())
    host = socket.gethostname()
    assert len(host) < 4 or host not in blob
    assert getpass.getuser() not in blob.split()
