"""Chapter 35 exercises. Complete each TODO, then run: python3 -m pytest test_exercises.py"""
from whitebox import Message, Model  # Provided: you'll need these.

JSON_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


def check_arguments(arguments, parameters):
    """TODO 1: The check whitebox is missing. parameters is a tool's JSON schema, such as
    {"type": "object", "properties": {"days": {"type": "integer"}}, "required": ["days"]}. Return None if arguments fit it, or one
    sentence for the model:
      "days is missing"                                    (a required name isn't in arguments)
      "days must be a integer, not 'three'"                (the value's Python type doesn't match JSON_TYPES; use repr for the value)
    Check the names in properties in order, and report the first problem. True and False are not integers here.
    """
    return None


def retry_once(call):
    """TODO 2: Call call() and return what it returns. If it raises an error whose retryable attribute is True, call it once more and
    return that, or let that second error out. Any other error goes straight out, without a second try.
    """
    return None


class Script(Model):
    """TODO 3: A scripted model, for testing any framework. steps is a list. Each step is a Message to give back, or an Exception
    to raise. chat records the messages it was sent in self.seen, then gives back or raises the next step. When the steps run out,
    give back Message("assistant", "(script ran out)").
    """

    def __init__(self, steps):
        self.steps = list(steps)
        self.seen = []

    def chat(self, messages, tools=None, **options):
        return None


def added_messages(sent, written):
    """TODO 4: Find what a framework added. sent is the list of messages a request carried, each a dict with "role" and "content".
    written is the list of (role, content) pairs you wrote. Return the sent messages, as (role, content) pairs, that you didn't write,
    in order.
    """
    return None


def scores(runs):
    """TODO 5: runs is a list of dicts with "framework", "visible" and "hidden". A run is fixed when both are True. Return
    {framework: "fixed/total"}, with the frameworks in the order they first appear.
    """
    return None
