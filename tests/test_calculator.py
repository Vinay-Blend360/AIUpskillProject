"""Tests for the calculator tool."""

from src.tools.calculator import calculator


def test_calculator_basic_arithmetic() -> None:
    assert calculator("2 + 3")["result"] == 5


def test_calculator_operator_precedence() -> None:
    assert calculator("2 + 3 * 4")["result"] == 14


def test_calculator_parentheses_and_power() -> None:
    assert calculator("(2 + 3) ** 2")["result"] == 25


def test_calculator_rejects_non_arithmetic() -> None:
    result = calculator("__import__('os').system('echo hi')")
    assert "error" in result


def test_calculator_rejects_name_lookup() -> None:
    result = calculator("os.getenv('HOME')")
    assert "error" in result
