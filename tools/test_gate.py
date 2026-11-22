"""The gate must reject entries that claim more than they show."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate  # noqa: E402


def first():
    entries = [x for x in gate.load_entries() if x[1]["status"] != "proposed"]
    assert entries, "no result entries found"
    return entries[0]


def test_all_entries_pass():
    for folder, e in gate.load_entries():
        assert gate.check_entry(folder, e) == [], folder


def test_confirmed_needs_every_criterion():
    folder, e = first()
    e = copy.deepcopy(e)
    e["status"] = "confirmed"
    if not all(e["gate"][c]["pass"] for c in gate.CRITERIA):
        assert any("confirmed" in m for m in gate.check_entry(folder, e))


def test_pass_without_evidence_is_rejected():
    folder, e = first()
    e = copy.deepcopy(e)
    e["gate"]["soundness_tests"] = {"pass": True, "evidence": "does/not/exist"}
    assert any("evidence path is missing" in m for m in gate.check_entry(folder, e))


def test_author_cannot_reproduce_own_entry():
    folder, e = first()
    e = copy.deepcopy(e)
    e["gate"]["independent_reproduction"] = {
        "pass": True,
        "evidence": "README.md",
        "by": e["authors"][0]["name"],
    }
    assert any("not an author" in m for m in gate.check_entry(folder, e))


def test_flagship_cannot_be_an_argument():
    folder, e = first()
    e = copy.deepcopy(e)
    e["flagship"]["kind"] = "argued"
    assert any("flagship.kind" in m for m in gate.check_entry(folder, e))


def test_machine_checked_claim_names_its_checker():
    folder, e = first()
    e = copy.deepcopy(e)
    e["claims"].append({"text": "x", "kind": "machine-checked", "evidence": "README.md"})
    assert any("checker" in m for m in gate.check_entry(folder, e))


def test_proposal_needs_refutation_condition_and_no_result():
    folder, e = first()
    e = copy.deepcopy(e)
    e["status"] = "proposed"
    msgs = gate.check_entry(folder, e)
    assert any("plan.refuted_if" in m for m in msgs)
    assert any("reports no result" in m for m in msgs)


def test_posted_upstream_link_needs_url():
    folder, e = first()
    e = copy.deepcopy(e)
    e["links"] = {"upstream": [{"target": "x", "state": "open"}]}
    assert any("needs a url" in m for m in gate.check_entry(folder, e))


def test_problem_cards_pass():
    for path, p in gate.load_problems():
        assert gate.check_problem(path, p) == [], path


def test_state_of_the_art_needs_a_source():
    path, p = gate.load_problems()[0]
    p = copy.deepcopy(p)
    p["state_of_the_art"].append(
        {"method": "m", "result": "r", "source": "trust me", "as_of": "2026-01-01"}
    )
    assert any("https link" in m for m in gate.check_problem(path, p))


def test_entry_needs_existing_problem_card():
    folder, e = first()
    e = copy.deepcopy(e)
    e["problem_card"] = "sat-pb/does-not-exist"
    assert any("problem_card not found" in m for m in gate.check_entry(folder, e))


def test_entry_improvement_dimension_is_from_the_fixed_list():
    folder, e = first()
    e = copy.deepcopy(e)
    e["improves"] = ["magic"]
    assert any("'improves'" in m for m in gate.check_entry(folder, e))
