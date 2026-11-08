"""Measure a run: tokens and time for every model call, and time spent in tools. Then decide what to cut."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .hooks import Hook


@dataclass
class Step:
    seconds: float
    tokens_in: int
    tokens_out: int
    tokens_cached: int = 0


class Meter(Hook):
    """Records every model call. prices is (input, output) in dollars per million tokens, or None for a free model."""

    def __init__(self, prices=None, clock=time.perf_counter):
        self.prices = prices
        self.clock = clock
        self.steps = []
        self.tool_seconds = 0.0

    def before_model(self, messages):
        self.model_started = self.clock()

    def after_model(self, reply):
        seconds = round(self.clock() - self.model_started, 3)
        self.steps.append(Step(seconds, reply.tokens_in, reply.tokens_out, reply.tokens_cached))

    def before_tool(self, call):
        self.tool_started = self.clock()

    def after_tool(self, call, output):
        self.tool_seconds += self.clock() - self.tool_started

    def cost(self):
        """Dollars, at full price. Cached tokens may have cost less."""
        if not self.prices:
            return 0.0
        price_in, price_out = self.prices
        return sum(step.tokens_in * price_in + step.tokens_out * price_out for step in self.steps) / 1_000_000

    def report(self):
        lines = [f"{'Call':<6}{'Tokens in':>10}{'Out':>6}{'Cached':>8}{'Seconds':>9}"]
        for number, step in enumerate(self.steps, 1):
            lines.append(f"{number:<6}{step.tokens_in:>10,}{step.tokens_out:>6}{step.tokens_cached:>8}{step.seconds:>9.2f}")
        model_seconds = sum(step.seconds for step in self.steps)
        lines.append(f"Model {model_seconds:.2f} s, tools {self.tool_seconds:.2f} s, cost ${self.cost():.6f}")
        return "\n".join(lines)


def where_tokens_go(messages, tools=()):
    """How many characters of each kind one model call sends. Characters, not tokens, but in the same proportion, roughly."""
    parts = {"system prompt": 0, "tool descriptions": 0, "question": 0, "tool results": 0, "model's own turns": 0}
    parts["tool descriptions"] = len(json.dumps([{"name": t.name, "description": t.description, "parameters": t.parameters} for t in tools]))
    for message in messages:
        if message.role == "system":
            parts["system prompt"] += len(message.content)
        elif message.role == "user":
            parts["question"] += len(message.content)
        elif message.role == "tool":
            parts["tool results"] += len(message.content)
        else:
            parts["model's own turns"] += len(message.content) + sum(len(c.name) + len(json.dumps(c.arguments)) for c in message.tool_calls)
    return parts


def run_many(make_agent, questions, workers=4):
    """Run each question on its own new agent, several at a time.

    Results come back in the order of the questions, whatever order they finish in.
    """
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(lambda question: make_agent().run(question), questions))
