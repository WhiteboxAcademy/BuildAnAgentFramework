"""Provided: build the agent our runs used, on any model, with a Meter on it, so each script can stay short.

A gemini/ model is wrapped in SpendLimit, so it stops at the limit. The prices are Google's paid rates on 8 November 2026, in dollars per
million tokens. Check https://aistudio.google.com/docs/pricing before you run anything, because they change.
"""
from library import OPTIONS, Remember, build_index
from whitebox import (
    AGENT_SYSTEM, Agent, LoopGuard, Meter, RescueToolCalls, Retry, SpendLimit, Toolbox, load_documents, load_env, load_model, search_tool,
)

PRICES = {"gemini-3.1-flash-lite": (0.25, 1.50), "gemini-3.6-flash": (0.75, 3.75)}
LIMIT = 0.50  # dollars, for everything this chapter's scripts send, added up in spend.json


def prices_of(spec):
    """The prices for a model string, or None for a model on your own computer."""
    return PRICES.get(spec.split("/", 1)[1]) if spec.startswith("gemini/") else None


def build_model(spec):
    load_env()
    model = load_model(spec)
    if spec.startswith("gemini/"):
        model = SpendLimit(Retry(model, attempts=6, delay=10), LIMIT, prices_of(spec), ledger="spend.json")
    return model


def build_agent(model, k=3, size=60, hooks=()):
    """One agent with one search over the handbook and the records. k is how many results each search returns, and size is how many
    words go in each chunk."""
    documents = load_documents("workspace/handbook") | load_documents("workspace/records")
    index = Remember(build_index(documents, size))
    options = OPTIONS | {"num_predict": 1024}
    return Agent(Retry(RescueToolCalls(model)), Toolbox([search_tool(index, k)]), system=AGENT_SYSTEM, options=options,
                 hooks=[*hooks, LoopGuard()])
