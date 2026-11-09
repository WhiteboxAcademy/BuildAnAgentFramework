"""Planning: write the steps first, then carry them out one at a time."""
import re

from .agent import Result
from .messages import Message
from .rag import RAG_SYSTEM, excerpts

PLAN = (
    "Question: {question}\n\nWrite a short plan for answering this from a staff handbook. List the facts to look up, "
    "in order, one per line, at most 3. A later step can use what an earlier step finds. Write nothing else."
)
QUERY = (
    "Step: {step}\n\nKnown so far:\n{known}\n\nWrite one short search query for this step, using what's known. "
    "Write nothing else."
)
FIND = (
    "Excerpts:\n\n{excerpts}\n\nStep: {step}\n\nIn one sentence, what do the excerpts say that answers this step? "
    "Use only the excerpts. If they don't say, reply: not found"
)
ONE_ANSWER = RAG_SYSTEM + " Give one answer for this person: don't list every option."


def clean(line):
    """Strip the bullets, numbering and quotes a model puts around a line, and keep the words themselves."""
    return re.sub(r'^[\s*"-]*(\d+[.)](?!\d)\s*)?', "", line).strip(' *".')


class Plan:
    """Write a plan, then search for each step, using what the earlier steps found."""

    def __init__(self, model, index, k=3, options=None):
        self.model = model
        self.index = index
        self.k = k
        self.options = options or {}

    def ask(self, text):
        return self.model.chat([Message("user", text)], **self.options).content.strip()

    def make_plan(self, question):
        lines = self.ask(PLAN.format(question=question)).splitlines()
        return [clean(line) for line in lines if clean(line)][:3]

    def run(self, question):
        steps = self.make_plan(question)
        hits, known, queries = [], [], []
        for step in steps:
            query = clean(self.ask(QUERY.format(step=step, known="\n".join(known)))) if known else step
            found = self.index.search(query, self.k)
            have = {hit.text for hit in hits}
            hits += [hit for hit in found if hit.text not in have]
            queries.append(query)
            known.append(self.ask(FIND.format(excerpts=excerpts(found), step=step)))
        notes = "\n".join(known)
        asked = f"Excerpts:\n\n{excerpts(hits)}\n\nNotes from the search:\n{notes}\n\nQuestion: {question}"
        messages = [Message("system", ONE_ANSWER), Message("user", asked)]
        reply = self.model.chat(messages, **self.options)
        result = Result(reply.content, messages + [reply], 2 * len(steps) + 1)
        result.plan, result.queries, result.seen = steps, queries, excerpts(hits)
        return result
