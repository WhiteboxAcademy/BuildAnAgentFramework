"""Durable execution: a run that can die and carry on, without doing anything twice."""
import json
import os
from dataclasses import asdict
from pathlib import Path

from .hooks import Hook
from .messages import Message, ToolCall
from .tools import Tool


class Checkpoint(Hook):
    """Save the conversation before each model call and after each tool, so a new process can pick it up."""

    def __init__(self, path):
        self.path = Path(path)
        self.messages = []

    def save(self, messages):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps([asdict(message) for message in messages]))
        os.replace(temporary, self.path)  # All or nothing: a crash can't leave half a file.

    def before_model(self, messages):
        self.messages = messages
        self.save(messages)

    def after_tool(self, call, output):
        self.save(self.messages + [Message("tool", output, tool_name=call.name)])

    def on_finish(self, result):
        if not result.stopped:
            self.path.unlink(missing_ok=True)  # A finished run has nothing to resume. A stopped one does.


def load_messages(path):
    """Read a checkpoint back, or return None if there's nothing to resume."""
    path = Path(path)
    if not path.exists():
        return None
    messages = []
    for data in json.loads(path.read_text()):
        data["tool_calls"] = [ToolCall(**call) for call in data["tool_calls"]]
        messages.append(Message(**data))
    return messages


def once(tool, done):
    """Make a tool safe to repeat. done(**arguments) asks the real system whether this already happened."""

    def guarded(**arguments):
        if done(**arguments):
            return f"Already done, so nothing changed: {arguments}"
        return tool(**arguments)

    return Tool(tool.name, tool.description, tool.parameters, guarded)


def until_done(agent, left, ask, history=None, tries=3):
    """Run until the real system says nothing is left, because a model can claim it finished when it didn't."""
    result = None
    for _ in range(tries):
        items = left()
        if not items:
            break
        result = agent.run(ask(items), history)
        history = result.messages
    return result
