"""Chapter 32 exercises. Complete each TODO, then run: python3 -m pytest test_exercises.py"""
from whitebox import ModelError


def gemini_part(message):
    """TODO 1: Turn one Message into Gemini's shape, as GeminiModel.to_gemini does for one message. Return a dictionary.
    A "user" message gives {"role": "user", "parts": [{"text": content}]}.
    An "assistant" message gives {"role": "model", "parts": [...]}, with {"text": content} first if there is any content, then
    {"functionCall": {"name": ..., "args": ...}} for each tool call.
    A "tool" message gives {"role": "user", "parts": [{"functionResponse": {"name": tool_name, "response": {"result": content}}}]}.
    """
    return None


def reply_cost(tokens_in, tokens_out, prices):
    """TODO 2: What one reply cost, in dollars. prices is (input, output), each in dollars per million tokens. Round to 6 places."""
    return None


def translate(options, names):
    """TODO 3: names maps our option names to a provider's, such as {"num_predict": "maxOutputTokens"}. Return a new dictionary with
    each option under the provider's name. If any option isn't in names, raise ValueError, and say which one. Never drop it quietly.
    """
    return None


def read_env_line(line):
    """TODO 4: One line of a .env file. Return (key, value), or None for a blank line, a comment (starting #) or a line with no =.
    Strip spaces around both, and remove one pair of quotes around the value, single or double. Split at the first = only.
    """
    return None


class Budget:
    """TODO 5: A spending limit. prices is (input, output) in dollars per million tokens.
    charge(tokens_in, tokens_out) adds what a reply cost to spent, using reply_cost.
    check() raises ModelError, with retryable False, once spent has reached dollars. Call it before each call, as SpendLimit does.
    """

    def __init__(self, dollars, prices):
        self.dollars = dollars
        self.prices = prices
        self.spent = 0.0

    def charge(self, tokens_in, tokens_out):
        pass

    def check(self):
        pass
