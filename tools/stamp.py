"""Print a machine stamp for benchmark evidence that describes the hardware class, not the machine.

Recorded: CPU model, core count, memory rounded to whole GB, operating system family, Python
version. Never recorded: host name, user name, serial numbers, addresses, paths.

Usage: python tools/stamp.py [--coarse]    # --coarse drops the CPU model string
"""

from __future__ import annotations

import json
import os
import platform
import sys


def cpu_model() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def memory_gb() -> int | None:
    try:
        pages, size = os.sysconf("SC_PHYS_PAGES"), os.sysconf("SC_PAGE_SIZE")
        return round(pages * size / 2**30)
    except (ValueError, OSError, AttributeError):
        return None


def stamp(coarse: bool = False) -> dict[str, object]:
    out: dict[str, object] = {
        "cpu": platform.machine() if coarse else cpu_model(),
        "cores": os.cpu_count(),
        "memory_gb": memory_gb(),
        "os": platform.system(),
        "python": platform.python_version(),
    }
    return out


if __name__ == "__main__":
    print(json.dumps(stamp("--coarse" in sys.argv), indent=2))
