"""Evaluate NewsFilterAgent's relevance judgments against a labeled golden dataset.

Run standalone: ``python -m src.evaluation.evaluator``
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from src.agents.news_filter_agent import NewsFilterAgent

DEFAULT_DATASET_PATH = "data/evaluation/golden_dataset.json"
DEFAULT_REPORT_PATH = "data/evaluation/evaluation_report.md"


class FilterEvaluator:
    """Runs the filter agent's relevance judgment against labeled test cases
    and computes accuracy/precision/recall/F1 against the expected labels.
    """

    def __init__(
        self,
        golden_dataset_path: str = DEFAULT_DATASET_PATH,
        agent: NewsFilterAgent | None = None,
    ) -> None:
        self.golden_dataset_path = golden_dataset_path
        self.agent = agent or NewsFilterAgent()

    async def evaluate(self) -> dict:
        dataset = json.loads(Path(self.golden_dataset_path).read_text(encoding="utf-8"))
        results = []

        for case in dataset["test_cases"]:
            judgment = await self.agent._judge_relevance(
                {"title": case["title"], "body": case["summary"]}
            )
            predicted_relevant = (
                judgment["relevant"]
                and judgment["relevance_score"] >= self.agent.relevance_threshold
            )
            results.append(
                {
                    **case,
                    "predicted_relevant": predicted_relevant,
                    "predicted_score": judgment["relevance_score"],
                    "reasoning": judgment["reasoning"],
                    "correct": predicted_relevant == case["expected_relevant"],
                }
            )

        return {"results": results, "metrics": self._calculate_metrics(results)}

    @staticmethod
    def _calculate_metrics(results: list[dict]) -> dict:
        total = len(results)
        correct = sum(1 for r in results if r["correct"])

        true_positives = sum(
            1 for r in results if r["expected_relevant"] and r["predicted_relevant"]
        )
        false_positives = sum(
            1 for r in results if r["predicted_relevant"] and not r["expected_relevant"]
        )
        false_negatives = sum(
            1 for r in results if r["expected_relevant"] and not r["predicted_relevant"]
        )

        accuracy = correct / total if total else 0.0
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives)
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives)
            else 0.0
        )
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "correct": correct,
            "total": total,
        }

    def save_report(self, evaluation: dict, report_path: str = DEFAULT_REPORT_PATH) -> Path:
        metrics = evaluation["metrics"]
        lines = [
            "# Filter Agent Evaluation Report",
            "",
            "## Overall Metrics",
            "",
            f"- **Accuracy:** {metrics['accuracy']:.1%} ({metrics['correct']}/{metrics['total']})",
            f"- **Precision:** {metrics['precision']:.1%}",
            f"- **Recall:** {metrics['recall']:.1%}",
            f"- **F1 Score:** {metrics['f1_score']:.3f}",
            "",
            "## Test Cases",
            "",
        ]

        for r in evaluation["results"]:
            status = "✅ PASS" if r["correct"] else "❌ FAIL"
            lines += [
                f"### {status}: {r['title']}",
                "",
                f"- Expected relevant: {r['expected_relevant']} (score {r['expected_score']})",
                f"- Predicted relevant: {r['predicted_relevant']} (score {r['predicted_score']})",
                f"- Reasoning: {r['reasoning']}",
                "",
            ]

        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


async def run_evaluation() -> dict:
    evaluator = FilterEvaluator()
    evaluation = await evaluator.evaluate()
    report_path = evaluator.save_report(evaluation)

    metrics = evaluation["metrics"]
    print(f"Accuracy:  {metrics['accuracy']:.1%}")
    print(f"Precision: {metrics['precision']:.1%}")
    print(f"Recall:    {metrics['recall']:.1%}")
    print(f"F1 Score:  {metrics['f1_score']:.3f}")
    print(f"Report saved to: {report_path}")

    return evaluation


if __name__ == "__main__":
    asyncio.run(run_evaluation())
