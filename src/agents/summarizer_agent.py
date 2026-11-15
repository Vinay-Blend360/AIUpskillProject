"""LLM agent that groups filtered articles by topic and summarizes each group."""

from __future__ import annotations

from collections import defaultdict

from src.agents.base_agent import BaseAgent
from src.storage.markdown_sections import load_sections, write_sections

_PROMPT_TEMPLATE = """Summarize these AI/ML news articles about "{topic}" in 3-5 bullet points \
for a daily digest. Be concise and factual.

{articles}
"""


class SummarizerAgent(BaseAgent):
    """Groups filtered articles by topic and produces a short digest per group."""

    async def _load_context(self, input_path: str) -> dict:
        return {"articles": load_sections(input_path)}

    async def _process(self, context: dict) -> dict:
        groups: dict[str, list[dict]] = defaultdict(list)
        for article in context["articles"]:
            topic = (article.get("key_topics", "").split(",")[0] or "General").strip()
            groups[topic or "General"].append(article)

        summaries = []
        for topic, articles in groups.items():
            summary = await self._summarize_topic(topic, articles)
            summaries.append({"topic": topic, "articles": articles, "summary": summary})

        return {"summaries": summaries}

    async def _summarize_topic(self, topic: str, articles: list[dict]) -> str:
        articles_text = "\n".join(f"- {a['title']}: {a.get('body', '')}" for a in articles)
        prompt = _PROMPT_TEMPLATE.format(topic=topic, articles=articles_text)
        return await self._call_llm(prompt)

    async def _save_result(self, result: dict, output_path: str) -> None:
        sections = [
            {
                "title": group["topic"],
                "article_count": len(group["articles"]),
                "body": group["summary"],
            }
            for group in result["summaries"]
        ]
        write_sections(output_path, sections, header="# Topic Summaries")
