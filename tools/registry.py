"""Write the registry table into README.md between the markers. --check fails if it is stale."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate  # noqa: E402

START, END = "<!-- registry:start -->", "<!-- registry:end -->"

if __name__ == "__main__":
    readme = gate.ROOT / "README.md"
    text = readme.read_text()
    a, b = text.index(START) + len(START), text.index(END)
    new = text[:a] + "\n" + gate.table(gate.load_entries()) + "\n" + text[b:]
    if "--check" in sys.argv:
        if new != text:
            print("README registry table is stale: run python tools/registry.py")
            sys.exit(1)
        print("registry table up to date")
    else:
        readme.write_text(new)
