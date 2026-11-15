"""Tests for FilterEvaluator."""

import json
from pathlib import Path

import pytest

from src.agents.news_filter_agent import NewsFilterAgent
from src.evaluation.evaluator import FilterEvaluator


def _write_dataset(tmp_path: Path, cases: list[dict]) -> Path:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps({"test_cases": cases}))
    return path


class _StubAgent(NewsFilterAgent):
    """Agent whose judgment is scripted per-title instead of calling an LLM."""

    def __init__(self, judgments: dict[str, dict]) -> None:
        super().__init__(relevance_threshold=6)
        self._judgments = judgments

    async def _judge_relevance(self, article: dict) -> dict:
        return self._judgments[article["title"]]


@pytest.mark.asyncio
async def test_metrics_computed_correctly(tmp_path: Path) -> None:
    cases = [
        {"id": 1, "title": "A", "summary": "x", "expected_relevant": True, "expected_score": 9},
        {"id": 2, "title": "B", "summary": "x", "expected_relevant": True, "expected_score": 8},
        {"id": 3, "title": "C", "summary": "x", "expected_relevant": False, "expected_score": 1},
        {"id": 4, "title": "D", "summary": "x", "expected_relevant": False, "expected_score": 1},
    ]
    judgments = {
        # A: correctly predicted relevant (TP)
        "A": {"relevant": True, "relevance_score": 9, "reasoning": "r"},
        # B: expected relevant but predicted not relevant (FN)
        "B": {"relevant": False, "relevance_score": 2, "reasoning": "r"},
        # C: correctly predicted not relevant (TN)
        "C": {"relevant": False, "relevance_score": 1, "reasoning": "r"},
        # D: expected not relevant but predicted relevant (FP)
        "D": {"relevant": True, "relevance_score": 8, "reasoning": "r"},
    }
    dataset_path = _write_dataset(tmp_path, cases)
    evaluator = FilterEvaluator(str(dataset_path), agent=_StubAgent(judgments))

    evaluation = await evaluator.evaluate()
    metrics = evaluation["metrics"]

    # TP=1 (A), FP=1 (D), FN=1 (B), TN=1 (C) -> accuracy 2/4
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1_score"] == pytest.approx(0.5)
    assert metrics["correct"] == 2
    assert metrics["total"] == 4


@pytest.mark.asyncio
async def test_save_report_writes_markdown(tmp_path: Path) -> None:
    cases = [
        {"id": 1, "title": "A", "summary": "x", "expected_relevant": True, "expected_score": 9},
    ]
    judgments = {"A": {"relevant": True, "relevance_score": 9, "reasoning": "clearly relevant"}}
    dataset_path = _write_dataset(tmp_path, cases)
    evaluator = FilterEvaluator(str(dataset_path), agent=_StubAgent(judgments))

    evaluation = await evaluator.evaluate()
    report_path = evaluator.save_report(evaluation, str(tmp_path / "report.md"))

    content = report_path.read_text()
    assert "Accuracy" in content
    assert "PASS" in content
    assert "clearly relevant" in content


@pytest.mark.asyncio
async def test_evaluate_against_real_golden_dataset_file() -> None:
    """The shipped golden_dataset.json must be loadable and well-formed."""
    judgments = {
        1: True,
        2: True,
        3: True,
        4: True,
        5: True,
        6: False,
        7: False,
        8: False,
        9: True,
        10: False,
    }

    class _AllCorrectAgent(NewsFilterAgent):
        async def _judge_relevance(self, article: dict) -> dict:
            return {"relevant": True, "relevance_score": 10, "reasoning": "stub"}

    evaluator = FilterEvaluator(agent=_AllCorrectAgent())
    dataset = json.loads(Path(evaluator.golden_dataset_path).read_text())

    assert len(dataset["test_cases"]) == 10
    assert set(judgments) == {case["id"] for case in dataset["test_cases"]}
