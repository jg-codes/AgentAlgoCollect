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
    if not all(e["gate"][c]["pass"] for c in gate.criteria(e)):
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


ENGINEERING_GATE = {
    "behaviour_preserved": {"pass": True, "evidence": "README.md"},
    "public_baseline": {"pass": True, "evidence": "README.md"},
    "one_command_reproduction": {"pass": True, "evidence": "README.md"},
    "second_machine": {"pass": False, "note": "one machine"},
    "upstream_offered": {"pass": False, "note": "not offered yet"},
    "independent_reproduction": {"pass": False, "note": "not rerun"},
}


def engineering_entry():
    folder, e = first()
    e = copy.deepcopy(e)
    e["track"] = "engineering"
    e["gate"] = copy.deepcopy(ENGINEERING_GATE)
    e["setting"] = {"hardware": "h", "software": "s", "data": "d"}
    return folder, e


def test_engineering_entry_with_its_own_criteria_passes():
    folder, e = engineering_entry()
    assert gate.check_entry(folder, e) == []


def test_engineering_entry_must_state_hardware_software_and_data():
    folder, e = engineering_entry()
    del e["setting"]
    assert any("setting.hardware" in m for m in gate.check_entry(folder, e))


def test_engineering_flagship_must_be_measured():
    folder, e = engineering_entry()
    e["flagship"]["kind"] = "machine-checked"
    assert any("flagship.kind" in m for m in gate.check_entry(folder, e))


def test_upstream_offered_needs_a_posted_link():
    folder, e = engineering_entry()
    e["gate"]["upstream_offered"] = {"pass": True, "evidence": "README.md"}
    e["links"] = {"upstream": [{"target": "x", "state": "planned"}]}
    assert any("no posted issue" in m for m in gate.check_entry(folder, e))


def test_criteria_from_another_track_are_rejected():
    folder, e = first()
    e = copy.deepcopy(e)
    e["gate"]["written_argument"] = {"pass": True, "evidence": "README.md"}
    assert any("do not belong to track" in m for m in gate.check_entry(folder, e))


def test_theory_entry_may_rest_on_an_argument_but_proof_needs_a_link():
    folder, e = first()
    e = copy.deepcopy(e)
    e["track"] = "theory"
    e["flagship"]["kind"] = "argued"
    e["gate"] = {
        "written_argument": {"pass": True, "evidence": "README.md"},
        "prior_work_check": {"pass": True, "evidence": "README.md"},
        "machine_checked_proof": {"pass": False, "note": "not formalized"},
        "independent_review": {"pass": False, "note": "not reviewed"},
    }
    e["links"] = {"upstream": [], "formal_proof": []}
    assert gate.check_entry(folder, e) == []
    e["gate"]["machine_checked_proof"] = {"pass": True, "evidence": "README.md"}
    assert any("links.formal_proof is empty" in m for m in gate.check_entry(folder, e))


def test_unknown_track_is_rejected():
    folder, e = first()
    e = copy.deepcopy(e)
    e["track"] = "magic"
    assert any("track must be one of" in m for m in gate.check_entry(folder, e))


def test_benchmark_cards_pass():
    cards = gate.load_benchmarks()
    assert cards
    for path, b in cards:
        assert gate.check_benchmark(path, b) == [], path


def test_own_benchmark_needs_a_generator():
    path, b = next(x for x in gate.load_benchmarks() if x[1]["kind"] == "own")
    b = copy.deepcopy(b)
    b["generator"] = "does/not/exist.py"
    assert any("generator" in m for m in gate.check_benchmark(path, b))


def test_flagship_needs_catalog_benchmark_and_setup():
    folder, e = first()
    e = copy.deepcopy(e)
    e["flagship"]["benchmark_id"] = "sat-pb/unknown"
    del e["flagship"]["setup"]["hardware"]
    msgs = gate.check_entry(folder, e)
    assert any("benchmark_id" in m for m in msgs)
    assert any("setup.hardware" in m for m in msgs)


def test_problem_card_benchmarks_must_be_in_catalog():
    path, p = gate.load_problems()[0]
    p = copy.deepcopy(p)
    p["benchmarks"] = ["sat-pb/unknown"]
    assert any("not found in catalog" in m for m in gate.check_problem(path, p))
