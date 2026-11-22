"""Check every problem card and entry against PROTOCOL.md.

Exit code 1 if anything claims more than it shows.

Usage: python tools/gate.py            # check everything
       python tools/gate.py --table    # print the registry tables (used by tools/registry.py)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

Entry = dict[str, Any]

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ("proposed", "candidate", "confirmed", "negative")

# Each track has its own criteria. The first `minimum` of them are needed for "candidate" or
# "negative", all of them for "confirmed". `kinds` are the claim kinds a flagship may have.
TRACKS: dict[str, dict[str, Any]] = {
    # Cannot be run or benchmarked today (for example quantum or asymptotic results).
    "theory": {
        "criteria": (
            "written_argument",
            "prior_work_check",
            "machine_checked_proof",
            "independent_review",
        ),
        "minimum": 2,
        "kinds": ("argued", "machine-checked"),
    },
    # A new or changed algorithm that runs today and is compared on a benchmark.
    "applied": {
        "criteria": (
            "soundness_tests",
            "public_baseline",
            "one_command_reproduction",
            "baseline_coverage",
            "real_benchmark_files",
            "second_machine",
            "independent_reproduction",
        ),
        "minimum": 3,
        "kinds": ("measured", "machine-checked"),
    },
    # Same algorithm and results, better implementation or better use of data and hardware.
    "engineering": {
        "criteria": (
            "behaviour_preserved",
            "public_baseline",
            "one_command_reproduction",
            "second_machine",
            "upstream_offered",
            "independent_reproduction",
        ),
        "minimum": 3,
        "kinds": ("measured",),
    },
}
# Criteria that must name a person who is not an author.
BY_OTHERS = ("independent_reproduction", "independent_review")

# How a claim is backed: run by code, checked by a proof checker, or argued in prose only.
KINDS = ("measured", "machine-checked", "argued")
LINK_STATES = ("planned", "open", "merged", "declined")
DIMENSIONS = (
    "speed",
    "quality",
    "robustness",
    "generality",
    "simplicity",
    "efficiency",
    "verifiability",
)
PROBLEM_FIELDS = (
    "id",
    "title",
    "domain",
    "as_of",
    "statement",
    "used_in",
    "benchmarks",
    "state_of_the_art",
    "pain_points",
    "open_dimensions",
)
BENCH_KINDS = ("public-suite", "paper", "generator", "own")
BENCH_FIELDS = (
    "id",
    "title",
    "domain",
    "kind",
    "url",
    "size",
    "measures",
    "protocol",
    "access",
    "as_of",
)
SETUP_FIELDS = ("time_limit", "threads", "hardware", "repeats")
COMMON = (
    "id",
    "title",
    "domain",
    "track",
    "status",
    "problem",
    "problem_card",
    "claim",
    "authors",
    "ai_assistance",
)
RESULT_FIELDS = ("improves", "flagship", "claims", "prior_work", "gate", "limits")


def load_entries() -> list[tuple[Path, Entry]]:
    out = []
    for f in sorted(ROOT.glob("entries/*/*/entry.yaml")):
        out.append((f.parent, yaml.safe_load(f.read_text()) or {}))
    return out


def load_problems() -> list[tuple[Path, Entry]]:
    return [
        (f, yaml.safe_load(f.read_text()) or {}) for f in sorted(ROOT.glob("problems/*/*.yaml"))
    ]


def load_benchmarks() -> list[tuple[Path, Entry]]:
    files = sorted(ROOT.glob("benchmarks/*/*.yaml"))
    return [(f, yaml.safe_load(f.read_text()) or {}) for f in files]


def check_benchmark(path: Path, b: Entry) -> list[str]:
    errs = [f"missing field: {k}" for k in BENCH_FIELDS if not b.get(k)]
    if errs:
        return errs
    if b["id"] != path.stem:
        errs.append(f"id '{b['id']}' differs from file name '{path.stem}'")
    if b["domain"] != path.parent.name:
        errs.append(f"domain '{b['domain']}' differs from folder '{path.parent.name}'")
    if b["kind"] not in BENCH_KINDS:
        errs.append(f"kind must be one of {BENCH_KINDS}")
    if not str(b["url"]).startswith("https://"):
        errs.append("url must be an https link")
    if b["kind"] == "own":
        if not b.get("generator") or not (ROOT / b["generator"]).exists():
            errs.append("an own benchmark needs a 'generator' path that exists in this repository")
        if "adopted_by" not in b:
            errs.append("an own benchmark needs an 'adopted_by' list (may be empty)")
    return errs


def _bench_exists(ref: str) -> bool:
    return (ROOT / "benchmarks" / f"{ref}.yaml").exists()


def criteria(e: Entry) -> tuple[str, ...]:
    crit: tuple[str, ...] = TRACKS[e["track"]]["criteria"]
    return crit


def check_problem(path: Path, p: Entry) -> list[str]:
    errs = [f"missing field: {k}" for k in PROBLEM_FIELDS if not p.get(k)]
    if errs:
        return errs
    if p["id"] != path.stem:
        errs.append(f"id '{p['id']}' differs from file name '{path.stem}'")
    if p["domain"] != path.parent.name:
        errs.append(f"domain '{p['domain']}' differs from folder '{path.parent.name}'")
    for ref in p["benchmarks"]:
        if not isinstance(ref, str) or not _bench_exists(ref):
            errs.append(f"benchmark not found in catalog: benchmarks/{ref}.yaml")
    for s in p["state_of_the_art"]:
        for k in ("method", "result", "source", "as_of"):
            if not s.get(k):
                errs.append(f"state_of_the_art item needs '{k}'")
        src = str(s.get("source", ""))
        if s.get("measured_here"):
            if not (ROOT / src).exists():
                errs.append(f"measured_here source not found in repository: {src}")
        elif not src.startswith("https://"):
            errs.append("state_of_the_art source must be an https link (or measured_here: true)")
    bad = [d for d in p["open_dimensions"] if d not in DIMENSIONS]
    if bad:
        errs.append(f"open_dimensions {bad} not in {DIMENSIONS}")
    if p.get("evaluator") and not (ROOT / p["evaluator"]).exists():
        errs.append(f"evaluator not found: {p['evaluator']}")
    return errs


def _exists(folder: Path, ref: str | list[str] | None) -> bool:
    """True if every reference is an https link or a file inside the entry."""
    if not ref:
        return False
    refs = [ref] if isinstance(ref, str) else ref
    return all(r.startswith("https://") or (folder / r).exists() for r in refs)


def _check_links(e: Entry) -> list[str]:
    errs = []
    links = e.get("links") or {}
    for u in links.get("upstream") or []:
        if u.get("state") not in LINK_STATES:
            errs.append(f"links.upstream state must be one of {LINK_STATES}")
        if u.get("state") != "planned" and not str(u.get("url", "")).startswith("https://"):
            errs.append("links.upstream needs a url unless its state is 'planned'")
    for p in links.get("formal_proof") or []:
        for k in ("system", "url", "commit", "statement"):
            if not p.get(k):
                errs.append(f"links.formal_proof needs '{k}'")
    return errs


def _check_gate(folder: Path, e: Entry) -> list[str]:
    errs = []
    gate, crit = e["gate"], criteria(e)
    for c in crit:
        item = gate.get(c)
        if not isinstance(item, dict) or "pass" not in item:
            errs.append(f"gate.{c} needs a 'pass' value")
        elif item["pass"]:
            if not _exists(folder, item.get("evidence")):
                errs.append(f"gate.{c} passes but its evidence path is missing")
        elif not item.get("note"):
            errs.append(f"gate.{c} does not pass and needs a 'note' saying why")
    unknown = sorted(set(gate) - set(crit))
    if unknown:
        errs.append(f"gate has criteria that do not belong to track '{e['track']}': {unknown}")
    authors = [a.get("name") for a in e["authors"]]
    for c in BY_OTHERS:
        item = gate.get(c) or {}
        if c in crit and item.get("pass") and (not item.get("by") or item["by"] in authors):
            errs.append(f"{c} must name someone who is not an author")
    posted = [
        u for u in (e.get("links") or {}).get("upstream") or [] if u.get("state") != "planned"
    ]
    if (
        "upstream_offered" in crit
        and (gate.get("upstream_offered") or {}).get("pass")
        and not posted
    ):
        errs.append(
            "upstream_offered passes but links.upstream has no posted issue or pull request"
        )
    proofs = (e.get("links") or {}).get("formal_proof") or []
    if "machine_checked_proof" in crit and (gate.get("machine_checked_proof") or {}).get("pass"):
        if not proofs:
            errs.append("machine_checked_proof passes but links.formal_proof is empty")
    passed = {c for c in crit if isinstance(gate.get(c), dict) and gate[c].get("pass")}
    minimum = set(crit[: TRACKS[e["track"]]["minimum"]])
    if e["status"] == "confirmed" and passed != set(crit):
        errs.append(f"'confirmed' needs every criterion; open: {sorted(set(crit) - passed)}")
    if e["status"] in ("candidate", "negative") and not minimum <= passed:
        errs.append(f"'{e['status']}' needs at least {sorted(minimum)}")
    return errs


def check_entry(folder: Path, e: Entry) -> list[str]:
    errs = [f"missing field: {k}" for k in COMMON if not e.get(k)]
    if errs:
        return errs
    if e["id"] != folder.name:
        errs.append(f"id '{e['id']}' differs from folder name '{folder.name}'")
    if e["domain"] != folder.parent.name:
        errs.append(f"domain '{e['domain']}' differs from folder '{folder.parent.name}'")
    if e["track"] not in TRACKS:
        return errs + [f"track must be one of {tuple(TRACKS)}"]
    if e["status"] not in STATUSES:
        return errs + [f"status must be one of {STATUSES}"]
    if not (folder / "README.md").exists():
        errs.append("README.md missing")
    if not (ROOT / "problems" / f"{e['problem_card']}.yaml").exists():
        errs.append(f"problem_card not found: problems/{e['problem_card']}.yaml")
    errs += _check_links(e)

    if e["status"] == "proposed":
        plan = e.get("plan") or {}
        for k in ("benchmark", "baseline", "refuted_if"):
            if not plan.get(k):
                errs.append(f"a proposal needs plan.{k}")
        if e.get("flagship"):
            errs.append("a proposal reports no result; remove 'flagship' or change the status")
        return errs

    missing = [f"missing field: {k}" for k in RESULT_FIELDS if not e.get(k)]
    if e["track"] != "theory" and not e.get("reproduce"):
        missing.append("missing field: reproduce")
    if e["track"] == "engineering":
        setting = e.get("setting") or {}
        missing += [
            f"engineering entries need setting.{k}"
            for k in ("hardware", "software", "data")
            if not setting.get(k)
        ]
    if missing:
        return errs + missing
    bad = [d for d in e["improves"] if d not in DIMENSIONS]
    if bad:
        errs.append(f"'improves' must list one or more of {DIMENSIONS}")
    fl = e["flagship"]
    for k in ("benchmark", "metric", "baseline", "ours", "evidence", "kind"):
        if not fl.get(k):
            errs.append(f"flagship.{k} missing")
    if e["track"] != "theory":
        if not _bench_exists(str(fl.get("benchmark_id"))):
            errs.append("flagship.benchmark_id must name a file under benchmarks/ (without .yaml)")
        setup = fl.get("setup") or {}
        errs += [f"flagship.setup.{k} missing" for k in SETUP_FIELDS if not setup.get(k)]
    allowed = TRACKS[e["track"]]["kinds"]
    if fl.get("kind") not in allowed:
        errs.append(f"flagship.kind must be one of {allowed} in track '{e['track']}'")
    if fl.get("evidence") and not _exists(folder, fl["evidence"]):
        errs.append(f"flagship.evidence path not found: {fl['evidence']}")
    for i, c in enumerate(e["claims"]):
        if c.get("kind") not in KINDS or not c.get("text"):
            errs.append(f"claims[{i}] needs 'text' and a 'kind' from {KINDS}")
        elif not _exists(folder, c.get("evidence")):
            errs.append(f"claims[{i}] ({c['kind']}) needs an evidence path or https link")
        elif c["kind"] == "machine-checked" and not c.get("checker"):
            errs.append(f"claims[{i}] is machine-checked and must name its 'checker'")
    return errs + _check_gate(folder, e)


def _backing(e: Entry) -> str:
    kinds = [c.get("kind") for c in e.get("claims", [])]
    return ", ".join(f"{kinds.count(k)} {k}" for k in KINDS if kinds.count(k))


def table(entries: list[tuple[Path, Entry]]) -> str:
    probs = [
        "| Problem | Domain | Benchmarks | Open dimensions | Evaluator | Entries |",
        "|---|---|---|---|---|---|",
    ]
    for path, p in load_problems():
        key = f"{p['domain']}/{p['id']}"
        n_e = sum(1 for _, e in entries if e.get("problem_card") == key)
        probs.append(
            f"| [{p['title']}]({path.relative_to(ROOT).as_posix()}) | {p['domain']} | "
            f"{', '.join(r.split('/')[-1] for r in p['benchmarks'])} | "
            f"{', '.join(p['open_dimensions'])} | {'yes' if p.get('evaluator') else 'no'} | {n_e} |"
        )
    out = "### Problems\n\n" + "\n".join(probs)
    cat = ["| Benchmark | Domain | Kind | Measures | Protocol |", "|---|---|---|---|---|"]
    for path, b in load_benchmarks():
        cat.append(
            f"| [{b['title']}]({path.relative_to(ROOT).as_posix()}) | {b['domain']} | "
            f"{b['kind']} | {'; '.join(b['measures'])} | {b['protocol']} |"
        )
    out += "\n\n### Benchmarks\n\n" + "\n".join(cat)
    for track in TRACKS:
        rows = [
            "| Entry | Status | Improves | Flagship result | Claims | Gate |",
            "|---|---|---|---|---|---|",
        ]
        for folder, e in entries:
            if e["track"] != track or e["status"] == "proposed":
                continue
            fl, crit = e["flagship"], criteria(e)
            n = sum(1 for c in crit if e["gate"].get(c, {}).get("pass"))
            rel = folder.relative_to(ROOT).as_posix()
            rows.append(
                f"| [{e['title']}]({rel}/) | {e['status']} | {', '.join(e['improves'])} | "
                f"{fl['benchmark']}: {fl['ours']} vs {fl['baseline']} | {_backing(e)} | "
                f"{n}/{len(crit)} |"
            )
        body = "\n".join(rows) if len(rows) > 2 else "No entries yet."
        out += f"\n\n### Results: {track}\n\n{body}"
    props = ["| Proposal | Track | Planned benchmark | Refuted if |", "|---|---|---|---|"]
    for folder, e in entries:
        if e["status"] == "proposed":
            plan = e["plan"]
            rel = folder.relative_to(ROOT).as_posix()
            props.append(
                f"| [{e['title']}]({rel}/) | {e['track']} | {plan['benchmark']} | "
                f"{plan['refuted_if']} |"
            )
    if len(props) > 2:
        out += "\n\n### Open proposals (no result yet)\n\n" + "\n".join(props)
    return out


if __name__ == "__main__":
    entries = load_entries()
    if "--table" in sys.argv:
        print(table(entries))
        sys.exit(0)
    bad = 0
    for path, b in load_benchmarks():
        errs = check_benchmark(path, b)
        print(("FAIL " if errs else "ok   ") + path.relative_to(ROOT).as_posix())
        for msg in errs:
            print("     - " + msg)
        bad += bool(errs)
    for path, p in load_problems():
        errs = check_problem(path, p)
        print(("FAIL " if errs else "ok   ") + path.relative_to(ROOT).as_posix())
        for msg in errs:
            print("     - " + msg)
        bad += bool(errs)
    for folder, e in entries:
        errs = check_entry(folder, e)
        print(("FAIL " if errs else "ok   ") + folder.relative_to(ROOT).as_posix())
        for msg in errs:
            print("     - " + msg)
        bad += bool(errs)
    sys.exit(1 if bad else 0)
