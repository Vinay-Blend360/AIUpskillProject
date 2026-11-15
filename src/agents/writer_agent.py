"""LLM agent that composes the final newsletter from the topic summaries."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.agents.base_agent import BaseAgent

_PROMPT_TEMPLATE = """Write a short, engaging daily AI/ML newsletter from these topic \
summaries. Use a friendly tone, a title, and one section per topic.

{summary_text}
"""


class WriterAgent(BaseAgent):
    """Turns the summarizer's output into a finished newsletter document."""

    async def _load_context(self, input_path: str) -> dict:
        return {"summary_text": Path(input_path).read_text(encoding="utf-8")}

    async def _process(self, context: dict) -> dict:
        prompt = _PROMPT_TEMPLATE.format(summary_text=context["summary_text"])
        newsletter = await self._call_llm(prompt)
        return {"newsletter": newsletter}

    async def _save_result(self, result: dict, output_path: str) -> None:
        date = datetime.now().strftime("%Y-%m-%d")
        content = f"{result['newsletter']}\n\n---\n*Generated {date}*\n"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
