"""Tools. @tool reads a function's type hints and docstring, so you describe it only once."""
import inspect
from dataclasses import dataclass
from typing import Annotated, Callable, get_args, get_origin, get_type_hints

JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean", dict: "object"}


def json_type(hint):
    """Turn a Python type hint into the JSON Schema that describes it."""
    if hint is list or get_origin(hint) is list:
        items = get_args(hint)
        return {"type": "array", "items": json_type(items[0])} if items else {"type": "array"}
    if hint not in JSON_TYPES:
        raise ValueError(f"Tools can't use the type {hint}")
    return {"type": JSON_TYPES[hint]}


def parameters_of(function):
    """Build the parameters schema from the function's signature."""
    hints = get_type_hints(function, include_extras=True)
    properties, required = {}, []
    for name, parameter in inspect.signature(function).parameters.items():
        hint = hints.get(name)
        if get_origin(hint) is not Annotated:
            raise ValueError(f'{function.__name__}: write {name} as Annotated[type, "description"]')
        kind, description = get_args(hint)
        properties[name] = {**json_type(kind), "description": description}
        if parameter.default is inspect.Parameter.empty:
            required.append(name)
    return {"type": "object", "properties": properties, "required": required}


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    function: Callable

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


def tool(function):
    """Turn a function into a Tool."""
    if not function.__doc__:
        raise ValueError(f"{function.__name__}: a tool needs a docstring")
    return Tool(function.__name__, inspect.getdoc(function), parameters_of(function), function)


class Toolbox:
    """The tools an agent can use."""

    def __init__(self, tools=()):
        self.tools = {tool.name: tool for tool in tools}

    def describe(self):
        """Describe the tools to a model."""
        return list(self.tools.values())

    def check(self, tool, arguments):
        """Return what's wrong with these arguments, or None."""
        parameters = tool.parameters
        missing = [name for name in parameters["required"] if name not in arguments]
        unknown = [name for name in arguments if name not in parameters["properties"]]
        if missing:
            return f"Error: {tool.name} needs {', '.join(missing)}"
        if unknown:
            return f"Error: {tool.name} doesn't take {', '.join(unknown)}"
        return None

    def run(self, call):
        """Run one tool call. Errors go back to the model as text so it can recover."""
        tool = self.tools.get(call.name)
        if tool is None:
            return f"Error: there is no tool called {call.name}. You have: {', '.join(self.tools)}"
        problem = self.check(tool, call.arguments)
        if problem:
            return problem
        try:
            return str(tool(**call.arguments))
        except Exception as error:
            return f"Error: {error}"
