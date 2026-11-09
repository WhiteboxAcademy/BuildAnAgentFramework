"""Things go wrong. These wrappers and hooks handle the failures we've actually seen."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import replace

from .hooks import Hook
from .messages import Message, ToolCall
from .models import Model, ModelError


def check_not_empty(reply):
    if not reply.content and not reply.tool_calls:
        raise ModelError("The model sent an empty reply.", retryable=True)
    return reply


class Retry(Model):
    """Wrap a model. Try again after a temporary failure, waiting longer each time."""

    def __init__(self, model, attempts=3, delay=1, sleep=time.sleep):
        self.model = model
        self.attempts = attempts
        self.delay = delay
        self.sleep = sleep

    def wait_or_raise(self, error, attempt):
        if not error.retryable or attempt == self.attempts:
            raise error
        self.sleep(self.delay * 2 ** (attempt - 1))

    def chat(self, messages, tools=None, **options):
        for attempt in range(1, self.attempts + 1):
            try:
                return check_not_empty(self.model.chat(messages, tools, **options))
            except ModelError as error:
                self.wait_or_raise(error, attempt)

    def stream(self, messages, tools=None, **options):
        for attempt in range(1, self.attempts + 1):
            started = False
            try:
                for piece in self.model.stream(messages, tools, **options):
                    if isinstance(piece, Message):
                        check_not_empty(piece)
                    started = True
                    yield piece
                return
            except ModelError as error:
                if started:  # The reader has seen part of a reply, so we can't start over.
                    raise
                self.wait_or_raise(error, attempt)


class Fallback(Model):
    """Try each model in turn until one works."""

    def __init__(self, models):
        self.models = models

    def chat(self, messages, tools=None, **options):
        for model in self.models[:-1]:
            try:
                return model.chat(messages, tools, **options)
            except ModelError:
                pass
        return self.models[-1].chat(messages, tools, **options)

    def stream(self, messages, tools=None, **options):
        for model in self.models[:-1]:
            started = False
            try:
                for piece in model.stream(messages, tools, **options):
                    started = True
                    yield piece
                return
            except ModelError:
                if started:
                    raise
        yield from self.models[-1].stream(messages, tools, **options)


def rescue(reply, tools):
    """If a model wrote a tool call as plain text, turn it into a real one."""
    if reply.tool_calls or not reply.content:
        return reply
    text = reply.content.replace("<tool_call>", "").replace("</tool_call>", "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return reply
    names = [tool.name for tool in tools or []]
    if not isinstance(data, dict) or data.get("name") not in names:
        return reply
    return replace(reply, content="", tool_calls=[ToolCall(data["name"], data.get("arguments", {}))])


class RescueToolCalls(Model):
    """Wrap a model, and rescue tool calls that were written as text."""

    def __init__(self, model):
        self.model = model

    def chat(self, messages, tools=None, **options):
        return rescue(self.model.chat(messages, tools, **options), tools)

    def stream(self, messages, tools=None, **options):
        for piece in self.model.stream(messages, tools, **options):
            yield rescue(piece, tools) if isinstance(piece, Message) else piece


class LoopGuard(Hook):
    """Block a tool call that exactly repeats earlier calls in the same run."""

    def __init__(self, limit=2):
        self.limit = limit
        self.counts = {}

    def before_tool(self, call):
        key = (call.name, json.dumps(call.arguments, sort_keys=True))
        self.counts[key] = self.counts.get(key, 0) + 1
        if self.counts[key] > self.limit:
            return f"Error: you've already made this exact call {self.limit} times. Try something else."
        return None

    def on_finish(self, result):
        self.counts = {}


def with_timeout(tool, seconds):
    """Return a copy of a tool that gives up after some seconds."""

    def limited(*args, **kwargs):
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(tool.function, *args, **kwargs)
        try:
            return future.result(timeout=seconds)
        except FutureTimeout:
            raise TimeoutError(f"{tool.name} took longer than {seconds} seconds") from None
        finally:
            pool.shutdown(wait=False)

    return replace(tool, function=limited)


class SpendLimit(Model):
    """Wrap a paid model. Count what each call costs, and refuse to call once the limit is reached.

    prices are dollars per million tokens, as (input, output). Output includes thinking. Pass ledger, a file name, to keep the
    total across runs, so the limit holds for a whole experiment, not just one script.
    """

    def __init__(self, model, dollars, prices, ledger=None):
        self.model = model
        self.dollars = dollars
        self.prices = prices
        self.ledger = ledger
        self.spent = json.load(open(ledger))["spent"] if ledger and os.path.exists(ledger) else 0.0

    def cost(self, reply):
        price_in, price_out = self.prices
        return (reply.tokens_in * price_in + reply.tokens_out * price_out) / 1_000_000

    def chat(self, messages, tools=None, **options):
        if self.spent >= self.dollars:
            said = f"Stopped: ${self.spent:.4f} spent, and the limit is ${self.dollars:.2f}."
            raise ModelError(said, retryable=False)
        reply = self.model.chat(messages, tools, **options)
        self.spent += self.cost(reply)
        if self.ledger:
            with open(self.ledger, "w") as file:
                json.dump({"spent": self.spent}, file)
        return reply
