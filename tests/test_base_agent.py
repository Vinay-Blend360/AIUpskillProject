"""Tests for BaseAgent's LLM-call plumbing and the execute() template method."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.base_agent import BaseAgent


class _EchoAgent(BaseAgent):
    """Minimal concrete agent for exercising the template method."""

    async def _load_context(self, input_path: str) -> dict:
        return {"input_path": input_path}

    async def _process(self, context: dict) -> dict:
        reply = await self._call_llm("say hi")
        return {"reply": reply, **context}

    async def _save_result(self, result: dict, output_path: str) -> None:
        self.saved = (result, output_path)


def _mock_completion_response(content: str, tool_calls=None) -> MagicMock:
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls
    message.model_dump.return_value = {"role": "assistant", "content": content}

    response = MagicMock()
    response.choices = [MagicMock(message=message)]
    return response


@pytest.mark.asyncio
async def test_execute_wires_load_process_save() -> None:
    agent = _EchoAgent()

    with patch(
        "src.agents.base_agent.acompletion",
        AsyncMock(return_value=_mock_completion_response("hello")),
    ):
        result = await agent.execute("in.md", "out.md")

    assert result["reply"] == "hello"
    assert result["input_path"] == "in.md"
    assert agent.saved == (result, "out.md")


@pytest.mark.asyncio
async def test_call_llm_with_tools_executes_tool_calls() -> None:
    agent = _EchoAgent()
    agent.register_tool_function("add", lambda a, b: a + b)

    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "add"
    tool_call.function.arguments = json.dumps({"a": 2, "b": 3})

    responses = [
        _mock_completion_response(None, tool_calls=[tool_call]),
        _mock_completion_response("The answer is 5"),
    ]

    with patch("src.agents.base_agent.acompletion", AsyncMock(side_effect=responses)):
        result = await agent._call_llm_with_tools([{"role": "user", "content": "add 2 and 3"}])

    assert result == "The answer is 5"


@pytest.mark.asyncio
async def test_call_llm_with_tools_raises_after_max_rounds() -> None:
    agent = _EchoAgent()
    agent.register_tool_function("noop", lambda: {})

    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "noop"
    tool_call.function.arguments = "{}"

    always_tool_calls = _mock_completion_response(None, tool_calls=[tool_call])

    with patch("src.agents.base_agent.acompletion", AsyncMock(return_value=always_tool_calls)):
        with pytest.raises(RuntimeError):
            await agent._call_llm_with_tools([{"role": "user", "content": "loop forever"}])
