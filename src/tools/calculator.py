"""A calculator tool an agent can call via function/tool-calling.

Evaluates arithmetic via an AST whitelist rather than ``eval()`` — the
expression comes from LLM output, which is untrusted input.
"""

from __future__ import annotations

import ast
import operator

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

CALCULATOR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression (+, -, *, /, %, **).",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "An arithmetic expression, e.g. '3 * (4 + 5)'.",
                }
            },
            "required": ["expression"],
        },
    },
}


def calculator(expression: str) -> dict:
    """Safely evaluate ``expression``. Returns ``{"result": ...}`` or ``{"error": ...}``."""
    try:
        tree = ast.parse(expression, mode="eval")
        return {"result": _eval_node(tree.body)}
    except Exception as e:  # noqa: BLE001 - surfacing any parse/eval failure to the caller
        return {"error": str(e)}


def _eval_node(node: ast.expr) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")
