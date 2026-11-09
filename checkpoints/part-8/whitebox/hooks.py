"""Hooks let you watch a run, or change it, without touching the loop."""
import json
import time
from dataclasses import asdict


class Hook:
    """Override the moments you care about. The rest do nothing."""

    def before_model(self, messages):
        pass

    def after_model(self, reply):
        pass

    def before_tool(self, call):
        """Return text to block this call. The model sees that text as the result."""
        return None

    def after_tool(self, call, output):
        pass

    def on_finish(self, result):
        pass


class Printer(Hook):
    """Show each tool call as it happens."""

    def before_tool(self, call):
        print(f"[tool] {call.name}({call.arguments})")

    def after_tool(self, call, output):
        print(f"    -> {output!r}")


class Approval(Hook):
    """Ask a person before running certain tools."""

    def __init__(self, names, ask=input):
        self.names = names
        self.ask = ask

    def before_tool(self, call):
        if call.name not in self.names:
            return None
        if self.ask(f"Allow {call.name}({call.arguments})? (y/n) ") == "y":
            return None
        return f"Error: a person refused the call to {call.name}"


class Tracer(Hook):
    """Write one line of JSON for each thing that happens, with timings and token counts."""

    def __init__(self, path, clock=time.monotonic):
        self.path = path
        self.clock = clock
        self.started = {}
        open(path, "w").close()

    def write(self, kind, **data):
        with open(self.path, "a") as file:
            file.write(json.dumps({"kind": kind, **data}) + "\n")

    def before_model(self, messages):
        self.started["model"] = self.clock()

    def after_model(self, reply):
        seconds = round(self.clock() - self.started["model"], 2)
        self.write("model", seconds=seconds, reply=asdict(reply))

    def before_tool(self, call):
        self.started["tool"] = self.clock()

    def after_tool(self, call, output):
        seconds = round(self.clock() - self.started["tool"], 3)
        self.write("tool", seconds=seconds, name=call.name, arguments=call.arguments, output=output)

    def on_finish(self, result):
        self.write("finish", answer=result.answer, steps=result.steps, stopped=result.stopped)


def show_trace(path):
    """Print a trace file so a person can read it."""
    tokens = seconds = 0
    with open(path) as file:
        for line in file:
            entry = json.loads(line)
            if entry["kind"] == "model":
                reply = entry["reply"]
                tokens += reply["tokens_in"] + reply["tokens_out"]
                seconds += entry["seconds"]
                wanted = ", ".join(call["name"] for call in reply["tool_calls"]) or "answer"
                print(f"model  {entry['seconds']:6.2f}s  {reply['tokens_in']:5} in {reply['tokens_out']:4} out  -> {wanted}")
            elif entry["kind"] == "tool":
                seconds += entry["seconds"]
                print(f"tool   {entry['seconds']:6.2f}s  {entry['name']}({entry['arguments']}) -> {entry['output']!r}")
            else:
                print(f"finish {seconds:6.2f}s  {tokens} tokens, {entry['steps']} steps: {entry['answer']}")
