from typing import Annotated

import pytest

from whitebox import ToolCall, Toolbox, tool


@tool
def scale(
    numbers: Annotated[list[float], "The numbers to scale"],
    factor: Annotated[int, "What to multiply by"] = 2,
) -> list:
    """Multiply each number."""
    return [number * factor for number in numbers]


def test_the_schema_comes_from_the_function():
    assert scale.name == "scale"
    assert scale.description == "Multiply each number."
    assert scale.parameters == {
        "type": "object",
        "properties": {
            "numbers": {"type": "array", "items": {"type": "number"}, "description": "The numbers to scale"},
            "factor": {"type": "integer", "description": "What to multiply by"},
        },
        "required": ["numbers"],
    }


def test_a_tool_is_still_callable():
    assert scale([1, 2], factor=3) == [3, 6]


def test_a_parameter_needs_a_description():
    with pytest.raises(ValueError, match="Annotated"):
        @tool
        def bad(path: str) -> str:
            """Do something."""


def test_a_tool_needs_a_docstring():
    with pytest.raises(ValueError, match="docstring"):
        @tool
        def bad(path: Annotated[str, "A path"]) -> str:
            return path


@pytest.mark.parametrize("call, expected", [
    (ToolCall("scale", {"numbers": [2]}), "[4]"),
    (ToolCall("fly", {}), "Error: there is no tool called fly. You have: scale"),
    (ToolCall("scale", {}), "Error: scale needs numbers"),
    (ToolCall("scale", {"numbers": [1], "size": 2}), "Error: scale doesn't take size"),
    (ToolCall("scale", {"numbers": "ab", "factor": None}), "Error: can't multiply sequence by non-int of type 'NoneType'"),
])
def test_the_toolbox_returns_results_and_errors_as_text(call, expected):
    assert Toolbox([scale]).run(call) == expected
