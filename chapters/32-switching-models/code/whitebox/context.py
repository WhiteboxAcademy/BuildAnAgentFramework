"""Context: keep a long conversation inside the window the model can read."""
import warnings

from .hooks import Hook
from .messages import Message

SUMMARY = (
    "Summarise this conversation for an assistant taking over. Keep every personal fact the user gave, such as "
    "names, numbers and days, exactly. Leave out handbook text.\n\n{text}"
)
NOTE = "\n\nEarlier in this conversation: "


def estimate_tokens(message):
    """A rough count: about four characters for each token, plus a little for the message itself."""
    return len(message.content) // 4 + 4


def total_tokens(messages):
    return sum(estimate_tokens(message) for message in messages)


def newest(messages, budget):
    """Return the newest messages that fit the budget, oldest first."""
    kept, used = [], 0
    for message in reversed(messages):
        used += estimate_tokens(message)
        if used > budget:
            break
        kept.insert(0, message)
    while kept and kept[0].role == "tool":
        kept.pop(0)  # A tool result makes no sense without the call that asked for it.
    return kept


class CutWarning(Hook):
    """Warn when the model read far fewer tokens than we sent, because the provider cut them silently."""

    def before_model(self, messages):
        self.sent = total_tokens(messages)

    def after_model(self, reply):
        if reply.tokens_in and reply.tokens_in < self.sent * 0.9:
            warnings.warn(f"Sent about {self.sent} tokens, but the model read {reply.tokens_in}.")


class Trim(Hook):
    """Before each model call, keep the system message and the newest messages that fit."""

    def __init__(self, budget):
        self.budget = budget

    def before_model(self, messages):
        if total_tokens(messages) > self.budget:
            system, rest = messages[:1], messages[1:]
            messages[:] = system + newest(rest, self.budget - total_tokens(system))


class Summarise(Hook):
    """Before each model call, fold the older messages into one note the model rewrites each round."""

    def __init__(self, model, budget, options=None):
        self.model = model
        self.budget = budget
        self.options = options or {}

    def before_model(self, messages):
        if total_tokens(messages) <= self.budget:
            return
        keep = newest(messages[1:], self.budget // 2)
        older = messages[1:len(messages) - len(keep)]
        system, _, note = messages[0].content.partition(NOTE)
        text = f"Earlier notes: {note}\n" if note else ""
        text += "\n".join(f"{message.role}: {message.content}" for message in older)
        reply = self.model.chat([Message("user", SUMMARY.format(text=text))], **self.options)
        messages[:] = [Message("system", system + NOTE + reply.content)] + keep
