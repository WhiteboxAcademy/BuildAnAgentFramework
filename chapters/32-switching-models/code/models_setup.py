"""Provided: build the agent our runs used, on any model, so each script can stay short.

A gemini/ model is wrapped in SpendLimit, so it stops at the limit. The prices are Google's paid rates in November 2026, in dollars per
million tokens. Check https://aistudio.google.com/docs/pricing before you run anything, because they change.
"""
from library import OPTIONS, Remember, build_index
from whitebox import (
    AGENT_SYSTEM, Agent, LoopGuard, Message, Model, RescueToolCalls, Retry, SpendLimit, Toolbox, load_documents, load_env, load_model,
    search_tool,
)

PRICES = {"gemini-3.1-flash-lite": (0.25, 1.50), "gemini-3.6-flash": (0.75, 3.75), "gemini-3.8-flash": (0.75, 3.75)}
LIMIT = 0.50  # dollars, for everything this chapter's scripts send, added up in spend.json
STOP_AFTER_CALL = " When you call a tool, write only the tool call, then stop and wait for its result."


class Counted(Model):
    """Counts the calls and tokens that pass through it."""

    def __init__(self, model):
        self.model = model
        self.calls = self.tokens_in = self.tokens_out = 0

    def chat(self, messages, tools=None, **options):
        reply = self.model.chat(messages, tools, **options)
        self.calls += 1
        self.tokens_in += reply.tokens_in
        self.tokens_out += reply.tokens_out
        return reply


def build_model(spec):
    """A model from a provider/name string. A paid one gets a spending limit and patient retries."""
    load_env()
    model = load_model(spec)
    if spec.startswith("gemini/"):
        model = SpendLimit(Retry(model, attempts=6, delay=10), LIMIT, PRICES[spec.split("/", 1)[1]], ledger="spend.json")
    return model


def build_agent(model, system=AGENT_SYSTEM):
    """One agent with one search over the handbook and the records, as in chapters 29 and 30."""
    documents = load_documents("workspace/handbook") | load_documents("workspace/records")
    index = Remember(build_index(documents, 60))
    options = OPTIONS | {"num_predict": 1024}  # a longest reply, as in chapter 30, for every provider
    return Agent(Retry(RescueToolCalls(model)), Toolbox([search_tool(index)]), system=system, options=options, hooks=[LoopGuard()])
