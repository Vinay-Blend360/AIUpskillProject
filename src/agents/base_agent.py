"""Abstract base for LLM-backed pipeline agents (Template Method pattern).

Every agent reads markdown produced by the previous stage, does its stage's
work, and writes markdown for the next stage. Subclasses only implement
``_load_context``/``_process``/``_save_result``; ``execute()`` wires them
together the same way for every agent.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Callable

from litellm import acompletion

DEFAULT_MODEL = "gemini/gemini-3.8-flash"
MAX_TOOL_ROUNDS = 10


class BaseAgent(ABC):
    """Common LLM-call plumbing (plain and tool-calling) for pipeline agents."""

    def __init__(self, model: str | None = None, tools: list[dict] | None = None) -> None:
        self.model = model or os.getenv("LITELLM_MODEL", DEFAULT_MODEL)
        self.tools = tools or []
        self.tool_functions: dict[str, Callable[..., Any]] = {}

    def register_tool_function(self, name: str, fn: Callable[..., Any]) -> None:
        """Make a Python callable available to the tool-calling loop under ``name``.

        ``name`` must match a function name declared in one of ``self.tools``'
        JSON-schema tool definitions.
        """
        self.tool_functions[name] = fn

    async def _call_llm(self, prompt: str, system: str | None = None) -> str:
        """Plain (no tool-calling) completion. Returns the assistant's text."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await acompletion(model=self.model, messages=messages)
        return response.choices[0].message.content or ""

    async def _call_llm_with_tools(self, messages: list[dict]) -> str:
        """Completion with a tool-calling loop: executes any requested tool calls
        and feeds results back to the model until it produces a final answer.
        """
        messages = list(messages)

        for _ in range(MAX_TOOL_ROUNDS):
            response = await acompletion(
                model=self.model, messages=messages, tools=self.tools or None
            )
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)

            if not tool_calls:
                return message.content or ""

            messages.append(message.model_dump())
            for tool_call in tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                fn = self.tool_functions.get(name)
                result = fn(**args) if fn else {"error": f"Unknown tool: {name}"}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(result),
                    }
                )

        raise RuntimeError(f"Exceeded {MAX_TOOL_ROUNDS} tool-calling rounds without a final answer")

    @abstractmethod
    async def _load_context(self, input_path: str) -> dict:
        """Load and parse whatever the previous stage produced at ``input_path``."""
        raise NotImplementedError

    @abstractmethod
    async def _process(self, context: dict) -> dict:
        """Do this agent's actual work, returning a result dict for ``_save_result``."""
        raise NotImplementedError

    @abstractmethod
    async def _save_result(self, result: dict, output_path: str) -> None:
        """Persist ``result`` to ``output_path`` for the next stage to read."""
        raise NotImplementedError

    async def execute(self, input_path: str, output_path: str) -> dict:
        """Template method: load -> process -> save, same shape for every agent."""
        context = await self._load_context(input_path)
        result = await self._process(context)
        await self._save_result(result, output_path)
        return result
