"""NewsFilterAgent variant that demonstrates LiteLLM function/tool calling.

Same relevance judgment as NewsFilterAgent, but asks the model to use the
`calculator` tool to compute a priority score from relevance + popularity,
rather than ever evaluating arithmetic itself.
"""

from __future__ import annotations

import json

from src.agents.news_filter_agent import RELEVANT_TOPICS, NewsFilterAgent
from src.tools.calculator import CALCULATOR_SCHEMA, calculator

_PROMPT_TEMPLATE = """You are an expert AI/ML news analyst with access to a calculator tool.

Title: {title}
Summary: {summary}
Popularity score: {score}

Relevant topics include: {topics}.

1. Judge relevance (0-10).
2. Use the calculator tool to compute priority = relevance_score * 2 + popularity_score / 10.

Once you have the priority value, respond with ONLY valid JSON (no markdown fences) matching:
{{"relevant": true or false, "relevance_score": integer 0-10, "reasoning": "one sentence", \
"key_topics": ["topic", ...], "priority": number}}
"""


class EnhancedFilterAgent(NewsFilterAgent):
    """Adds tool-calling (a calculator) to the relevance-judgment step."""

    def __init__(self, relevance_threshold: int = 6, model: str | None = None) -> None:
        super().__init__(relevance_threshold=relevance_threshold, model=model)
        self.tools = [CALCULATOR_SCHEMA]
        self.register_tool_function("calculator", calculator)

    async def _judge_relevance(self, article: dict) -> dict:
        prompt = _PROMPT_TEMPLATE.format(
            title=article.get("title", ""),
            summary=article.get("body", ""),
            score=article.get("score", 0),
            topics=", ".join(RELEVANT_TOPICS),
        )

        try:
            raw = await self._call_llm_with_tools([{"role": "user", "content": prompt}])
            cleaned = (
                raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            )
            judgment = json.loads(cleaned)
            if not {"relevant", "relevance_score", "reasoning"} <= judgment.keys():
                raise ValueError(f"Missing required keys in judgment: {judgment}")
            judgment.setdefault("key_topics", [])
            return judgment
        except Exception as e:  # noqa: BLE001 - any parse/LLM/tool failure degrades safely
            return {
                "relevant": False,
                "relevance_score": 0,
                "reasoning": f"Failed to judge: {e}",
                "key_topics": [],
            }
