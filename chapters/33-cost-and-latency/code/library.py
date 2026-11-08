"""Provided helpers for this chapter's scripts, so each script can stay short."""
import json
import re
from pathlib import Path

from whitebox import (
    AGENT_SYSTEM, Agent, HybridIndex, Index, KeywordIndex, LoopGuard, OllamaEmbedder, RescueToolCalls, Retry, Toolbox,
    load_documents, make_chunks, search_tool,
)

OPTIONS = {"temperature": 0.7}


def all_documents():
    """The handbook and the records, in one dictionary of name to text."""
    return load_documents("workspace/handbook") | load_documents("workspace/records")


def build_index(documents, size, titles=True):
    """Chunk the documents, with titles on, embed the chunks, and return the vector Index."""
    index = Index(OllamaEmbedder())
    index.add(make_chunks(documents, size, titles))
    return index


def build_hybrid(documents, size, titles=True):
    """The same chunks in a vector index and a keyword index, joined by a HybridIndex."""
    index = HybridIndex([Index(OllamaEmbedder()), KeywordIndex()])
    index.add(make_chunks(documents, size, titles))
    return index


def build_agent(model, index, k=3, system=AGENT_SYSTEM):
    """The agent from agent_ask.py: chapter 17's safety nets, and one tool that searches this index."""
    return Agent(
        Retry(RescueToolCalls(model)),
        Toolbox([search_tool(index, k)]),
        system=system,
        options=OPTIONS,
        hooks=[LoopGuard()],
    )


def searches(result):
    """The query of every search the agent chose, in order."""
    return [call.arguments.get("query", "") for message in result.messages for call in message.tool_calls]


def tool_text(result):
    """Everything the searches sent back, as one string."""
    return "\n\n".join(message.content for message in result.messages if message.role == "tool")


def files_seen(text):
    """The file names in search results, which excerpts writes as [name.md] on their own lines."""
    return sorted(set(re.findall(r"^\[(.+\.md)\]$", text, re.MULTILINE)))


class Keep:
    """Wraps an agent or a pipeline for run_eval, and keeps what each run did, which a Report doesn't."""

    def __init__(self, runner):
        self.runner = runner
        self.runs = []

    def run(self, question):
        result = self.runner.run(question)
        self.runs.append({
            "question": question,
            "answer": result.answer,
            "steps": result.steps,
            "stopped": result.stopped,
            "tokens_in": sum(message.tokens_in for message in result.messages),
            "searches": getattr(result, "queries", None) or searches(result),
            "seen": getattr(result, "seen", None) or tool_text(result),
        })
        return result

    def save(self, path):
        with open(path, "w") as file:
            json.dump(self.runs, file, indent=1)


def saved(name):
    """Your own results file if you've made one, and otherwise our saved one in results/."""
    return name if Path(name).exists() else f"results/{name}"


def load_runs(name):
    with open(saved(name)) as file:
        return json.load(file)


class Remember:
    """Keeps each search result, so repeat runs of the same search don't embed it again."""

    def __init__(self, index):
        self.index = index
        self.seen = {}

    def search(self, question, k=5):
        if (question, k) not in self.seen:
            self.seen[(question, k)] = self.index.search(question, k)
        return self.seen[(question, k)]
