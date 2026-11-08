"""Provided: the setups this chapter compares, so each script can stay short."""
from typing import Annotated

from library import OPTIONS, Remember, build_index
from whitebox import (
    AGENT_SYSTEM, Agent, LoopGuard, Message, Model, RescueToolCalls, Retry, Router, Toolbox, agent_tool, load_documents, search_tool,
    tool,
)
from whitebox.rag import excerpts

RECORDS_SYSTEM = (AGENT_SYSTEM.replace("the Quillon Coffee staff handbook", "Quillon Coffee's records: branch logs, suppliers and products")
                  .replace("search_handbook", "search_records"))
TWO_TOOLS_SYSTEM = (AGENT_SYSTEM.replace("the Quillon Coffee staff handbook", "Quillon Coffee")
                    .replace("Use search_handbook to find facts", "Use search_handbook for staff rules and search_records for branch "
                             "logs, suppliers and products"))
MANAGER_SYSTEM = (
    "You answer questions from Quillon Coffee staff, and you have two colleagues. ask_handbook knows the staff handbook. "
    "ask_records knows branch logs, suppliers and products. Pass the question to the right colleague, with every detail, "
    "then give their answer. Never answer from memory. If they can't find it, say exactly: I don't know."
)
STRICT_MANAGER = MANAGER_SYSTEM + (
    " You know nothing yourself, so always ask a colleague first, even if the question looks unclear or is only a code. "
    "If the first colleague can't find it, ask the other one before you say I don't know."
)
HANDBOOK_JOB = "Staff rules: pay, leave, uniform, safety, forms, error codes and how each branch works."
RECORDS_JOB = "Branch logs of past events, suppliers, and product prices."


class Counted(Model):
    """Sits under everything, so it counts every model call a team makes, however deep."""

    def __init__(self, model):
        self.model = model
        self.calls = self.tokens_in = 0

    def add(self, reply):
        self.calls += 1
        self.tokens_in += reply.tokens_in

    def chat(self, messages, tools=None, **options):
        reply = self.model.chat(messages, tools, **options)
        self.add(reply)
        return reply

    def stream(self, messages, tools=None, **options):
        for piece in self.model.stream(messages, tools, **options):
            if isinstance(piece, Message):
                self.add(piece)
            yield piece


def records_tool(index, k=3):
    @tool
    def search_records(query: Annotated[str, "What to look up, in a few words"]) -> str:
        """Search branch logs, suppliers and products. Search again with new words if the result isn't enough."""
        return excerpts(index.search(query, k)) or "Nothing found."

    return search_records


def make_agent(model, tools, system):
    return Agent(Retry(RescueToolCalls(model)), Toolbox(tools), system=system, options=OPTIONS, hooks=[LoopGuard()])


class Setups:
    """Three indexes, built once: everything, the handbook only and the records only."""

    def __init__(self, model):
        self.model = model
        handbook = load_documents("workspace/handbook")
        records = load_documents("workspace/records")
        self.everything = Remember(build_index(handbook | records, 60))
        self.handbook = Remember(build_index(handbook, 60))
        self.records = Remember(build_index(records, 60))

    def workers(self):
        return (make_agent(self.model, [search_tool(self.handbook)], AGENT_SYSTEM),
                make_agent(self.model, [records_tool(self.records)], RECORDS_SYSTEM))

    def one_agent(self):
        return make_agent(self.model, [search_tool(self.everything)], AGENT_SYSTEM)

    def two_tools(self):
        return make_agent(self.model, [search_tool(self.handbook), records_tool(self.records)], TWO_TOOLS_SYSTEM)

    def router(self):
        book, logs = self.workers()
        return Router(Retry(self.model), {"handbook": (HANDBOOK_JOB, book), "records": (RECORDS_JOB, logs)})

    def manager(self, system=MANAGER_SYSTEM):
        book, logs = self.workers()
        return make_agent(self.model, [agent_tool(book, "ask_handbook", "Ask the colleague who knows the staff handbook."),
                                       agent_tool(logs, "ask_records", "Ask the colleague who knows branch logs, suppliers and products.")],
                          system)
