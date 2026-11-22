"""Check every entry against PROTOCOL.md. Exit code 1 if any entry claims more than it shows.

Usage: python tools/gate.py            # check all entries
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
CRITERIA = (
    "soundness_tests",
    "public_baseline",
    "one_command_reproduction",
    "baseline_coverage",
    "real_benchmark_files",
    "second_machine",
    "independent_reproduction",
)
# A candidate must at least be correct, compared fairly and reproducible.
CANDIDATE_MIN = CRITERIA[:3]
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
COMMON = (
    "id",
    "title",
    "domain",
    "status",
    "problem",
    "problem_card",
    "claim",
    "authors",
    "ai_assistance",
)
RESULT_FIELDS = ("flagship", "claims", "prior_work", "reproduce", "gate", "limits")


def load_entries() -> list[tuple[Path, Entry]]:
    out = []
    for f in sorted(ROOT.glob("entries/*/*/entry.yaml")):
        out.append((f.parent, yaml.safe_load(f.read_text()) or {}))
    return out


def load_problems() -> list[tuple[Path, Entry]]:
    return [
        (f, yaml.safe_load(f.read_text()) or {}) for f in sorted(ROOT.glob("problems/*/*.yaml"))
    ]


def check_problem(path: Path, p: Entry) -> list[str]:
    errs = [f"missing field: {k}" for k in PROBLEM_FIELDS if not p.get(k)]
    if errs:
        return errs
    if p["id"] != path.stem:
        errs.append(f"id '{p['id']}' differs from file name '{path.stem}'")
    if p["domain"] != path.parent.name:
        errs.append(f"domain '{p['domain']}' differs from folder '{path.parent.name}'")
    for b in p["benchmarks"]:
        for k in ("name", "kpis", "protocol"):
            if not b.get(k):
                errs.append(f"benchmark needs '{k}'")
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


def check_entry(folder: Path, e: Entry) -> list[str]:
    errs = [f"missing field: {k}" for k in COMMON if not e.get(k)]
    if errs:
        return errs
    if e["id"] != folder.name:
        errs.append(f"id '{e['id']}' differs from folder name '{folder.name}'")
    if e["domain"] != folder.parent.name:
        errs.append(f"domain '{e['domain']}' differs from folder '{folder.parent.name}'")
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

    errs += [f"missing field: {k}" for k in RESULT_FIELDS if not e.get(k)]
    if errs:
        return errs
    bad = [d for d in e.get("improves") or [] if d not in DIMENSIONS]
    if bad or not e.get("improves"):
        errs.append(f"'improves' must list one or more of {DIMENSIONS}")
    fl = e["flagship"]
    for k in ("benchmark", "metric", "baseline", "ours", "evidence", "kind"):
        if not fl.get(k):
            errs.append(f"flagship.{k} missing")
    if fl.get("kind") not in ("measured", "machine-checked"):
        errs.append("flagship.kind must be 'measured' or 'machine-checked', not an argument")
    if fl.get("evidence") and not _exists(folder, fl["evidence"]):
        errs.append(f"flagship.evidence path not found: {fl['evidence']}")
    for i, c in enumerate(e["claims"]):
        if c.get("kind") not in KINDS or not c.get("text"):
            errs.append(f"claims[{i}] needs 'text' and a 'kind' from {KINDS}")
        elif not _exists(folder, c.get("evidence")):
            errs.append(f"claims[{i}] ({c['kind']}) needs an evidence path or https link")
        elif c["kind"] == "machine-checked" and not c.get("checker"):
            errs.append(f"claims[{i}] is machine-checked and must name its 'checker'")
    gate = e["gate"]
    for c in CRITERIA:
        item = gate.get(c)
        if not isinstance(item, dict) or "pass" not in item:
            errs.append(f"gate.{c} needs a 'pass' value")
        elif item["pass"]:
            if not _exists(folder, item.get("evidence")):
                errs.append(f"gate.{c} passes but its evidence path is missing")
        elif not item.get("note"):
            errs.append(f"gate.{c} does not pass and needs a 'note' saying why")
    rep = gate.get("independent_reproduction") or {}
    if rep.get("pass"):
        if not rep.get("by") or rep["by"] in [a.get("name") for a in e["authors"]]:
            errs.append("independent_reproduction must name someone who is not an author")
    passed = {c for c in CRITERIA if isinstance(gate.get(c), dict) and gate[c].get("pass")}
    if e["status"] == "confirmed" and passed != set(CRITERIA):
        errs.append(f"'confirmed' needs every criterion; open: {sorted(set(CRITERIA) - passed)}")
    if e["status"] in ("candidate", "negative") and not set(CANDIDATE_MIN) <= passed:
        errs.append(f"'{e['status']}' needs at least {list(CANDIDATE_MIN)}")
    return errs


def _backing(e: Entry) -> str:
    kinds = [c.get("kind") for c in e.get("claims", [])]
    return ", ".join(f"{kinds.count(k)} {k}" for k in KINDS if kinds.count(k))


def table(entries: list[tuple[Path, Entry]]) -> str:
    probs = [
        "| Problem | Domain | Benchmark and measures | Open dimensions | Entries |",
        "|---|---|---|---|---|",
    ]
    for path, p in load_problems():
        key = f"{p['domain']}/{p['id']}"
        n_e = sum(1 for _, e in entries if e.get("problem_card") == key)
        b = p["benchmarks"][0]
        probs.append(
            f"| [{p['title']}]({path.relative_to(ROOT).as_posix()}) | {p['domain']} | "
            f"{b['name']}: {'; '.join(b['kpis'])} | {', '.join(p['open_dimensions'])} | {n_e} |"
        )
    rows = [
        "| Entry | Status | Improves | Flagship result | Claims | Gate |",
        "|---|---|---|---|---|---|",
    ]
    props = ["| Proposal | Domain | Planned benchmark | Refuted if |", "|---|---|---|---|"]
    for folder, e in entries:
        rel = folder.relative_to(ROOT).as_posix()
        if e["status"] == "proposed":
            plan = e["plan"]
            props.append(
                f"| [{e['title']}]({rel}/) | {e['domain']} | {plan['benchmark']} | "
                f"{plan['refuted_if']} |"
            )
            continue
        fl = e["flagship"]
        n = sum(1 for c in CRITERIA if e["gate"].get(c, {}).get("pass"))
        rows.append(
            f"| [{e['title']}]({rel}/) | {e['status']} | {', '.join(e['improves'])} | "
            f"{fl['benchmark']}: {fl['ours']} vs {fl['baseline']} | {_backing(e)} | "
            f"{n}/{len(CRITERIA)} |"
        )
    out = "### Problems\n\n" + "\n".join(probs) + "\n\n### Results\n\n" + "\n".join(rows)
    if len(props) > 2:
        out += "\n\n### Open proposals (no result yet)\n\n" + "\n".join(props)
    return out


if __name__ == "__main__":
    entries = load_entries()
    if "--table" in sys.argv:
        print(table(entries))
        sys.exit(0)
    bad = 0
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
