"""LLM agent that judges whether each fetched article is AI/ML-relevant."""

from __future__ import annotations

import json

from src.agents.base_agent import BaseAgent
from src.storage.markdown_sections import load_sections, write_sections

RELEVANT_TOPICS = [
    "Machine Learning",
    "LLMs",
    "Neural Networks",
    "Computer Vision",
    "NLP",
    "AI Research",
    "AI Applications",
    "Deep Learning",
    "Transformers",
    "GPT",
    "Stable Diffusion",
    "AI Ethics",
    "AI Safety",
]

_PROMPT_TEMPLATE = """You are an expert AI/ML news analyst. Judge whether the following \
article is relevant to AI/ML news readers.

Title: {title}
Summary: {summary}

Relevant topics include: {topics}.

Examples:
- "OpenAI releases GPT-4 with improved reasoning" -> relevant, score 9
- "New JavaScript framework released" -> not relevant, score 1

Output ONLY valid JSON (no markdown fences, no commentary) matching exactly:
{{"relevant": true or false, "relevance_score": integer 0-10, "reasoning": "one sentence", \
"key_topics": ["topic", ...]}}
"""


class NewsFilterAgent(BaseAgent):
    """Keeps articles the LLM judges relevant to AI/ML, above a score threshold."""

    def __init__(self, relevance_threshold: int = 6, model: str | None = None) -> None:
        super().__init__(model=model)
        self.relevance_threshold = relevance_threshold

    async def _load_context(self, input_path: str) -> dict:
        return {"articles": load_sections(input_path)}

    async def _process(self, context: dict) -> dict:
        articles = context["articles"]
        filtered = []

        for article in articles:
            judgment = await self._judge_relevance(article)
            if judgment["relevant"] and judgment["relevance_score"] >= self.relevance_threshold:
                filtered.append({**article, **judgment})

        return {
            "filtered_articles": filtered,
            "total_input": len(articles),
            "total_output": len(filtered),
        }

    async def _judge_relevance(self, article: dict) -> dict:
        prompt = _PROMPT_TEMPLATE.format(
            title=article.get("title", ""),
            summary=article.get("body", ""),
            topics=", ".join(RELEVANT_TOPICS),
        )

        try:
            raw = await self._call_llm(prompt)
            cleaned = (
                raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            )
            judgment = json.loads(cleaned)
            if not {"relevant", "relevance_score", "reasoning"} <= judgment.keys():
                raise ValueError(f"Missing required keys in judgment: {judgment}")
            judgment.setdefault("key_topics", [])
            return judgment
        except Exception as e:  # noqa: BLE001 - any parse/LLM failure degrades to "not relevant"
            return {
                "relevant": False,
                "relevance_score": 0,
                "reasoning": f"Failed to judge: {e}",
                "key_topics": [],
            }

    async def _save_result(self, result: dict, output_path: str) -> None:
        filtered = result["filtered_articles"]
        filter_rate = (
            f"{result['total_output'] / result['total_input']:.1%}"
            if result["total_input"]
            else "n/a"
        )
        header = (
            "# Filtered Articles\n\n"
            f"**Input:** {result['total_input']} articles  \n"
            f"**Kept:** {result['total_output']} articles  \n"
            f"**Filter rate:** {filter_rate}"
        )

        sections = [
            {
                "title": article["title"],
                "url": article.get("url", ""),
                "relevance_score": article["relevance_score"],
                "key_topics": ", ".join(article.get("key_topics", [])),
                "body": article["reasoning"],
            }
            for article in filtered
        ]
        write_sections(output_path, sections, header=header)
