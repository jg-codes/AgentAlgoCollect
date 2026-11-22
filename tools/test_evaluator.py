"""The evaluator must be deterministic and must void the score of a wrong candidate."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "evaluator", ROOT / "evaluators" / "sat-pb" / "hidden_counting_in_clauses.py"
)
assert spec and spec.loader
evaluator = importlib.util.module_from_spec(spec)
sys.modules["evaluator"] = evaluator
spec.loader.exec_module(evaluator)


def candidate(tmp_path: Path, answer_line: str) -> str:
    path = tmp_path / "candidate.py"
    path.write_text(f"print({answer_line!r})\n")
    return str(path)


def test_instances_are_deterministic_and_labelled():
    a, b = evaluator.instances(), evaluator.instances()
    assert a == b
    assert len(a) == 15
    assert sum(1 for x in a if x[1] == "SATISFIABLE") == 3


def test_always_unsat_is_voided_by_the_controls(tmp_path):
    result = evaluator.evaluate(candidate(tmp_path, "s UNSATISFIABLE"))
    assert result["wrong_answers"] == 3
    assert result["combined_score"] == 0.0


def test_no_answer_scores_zero_without_being_wrong(tmp_path):
    result = evaluator.evaluate(candidate(tmp_path, "c no idea"))
    assert result["solved"] == 0 and result["wrong_answers"] == 0
    assert result["combined_score"] == 0.0
