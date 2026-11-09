"""Worked answers for chapter 35's exercises."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))  # Provided: finds code/whitebox.

from whitebox import Message, Model

JSON_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


def check_arguments(arguments, parameters):
    for name, schema in parameters.get("properties", {}).items():
        if name not in arguments:
            if name in parameters.get("required", []):
                return f"{name} is missing"
            continue
        value, kind = arguments[name], schema.get("type")
        wrong_bool = isinstance(value, bool) and kind in ("integer", "number")
        if kind in JSON_TYPES and (wrong_bool or not isinstance(value, JSON_TYPES[kind])):
            return f"{name} must be a {kind}, not {value!r}"
    return None


def retry_once(call):
    try:
        return call()
    except Exception as error:
        if getattr(error, "retryable", False) is not True:
            raise
    return call()


class Script(Model):
    def __init__(self, steps):
        self.steps = list(steps)
        self.seen = []

    def chat(self, messages, tools=None, **options):
        self.seen.append(list(messages))
        if not self.steps:
            return Message("assistant", "(script ran out)")
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def added_messages(sent, written):
    return [(m["role"], m["content"]) for m in sent if (m["role"], m["content"]) not in written]


def scores(runs):
    table = {}
    for run in runs:
        done, total = table.get(run["framework"], (0, 0))
        table[run["framework"]] = (done + (run["visible"] and run["hidden"]), total + 1)
    return {framework: f"{done}/{total}" for framework, (done, total) in table.items()}
