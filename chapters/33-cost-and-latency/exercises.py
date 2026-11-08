"""Chapter 33 exercises. Complete each TODO, then run: python3 -m pytest test_exercises.py"""
from concurrent.futures import ThreadPoolExecutor  # Provided: you'll need this.

from whitebox import Hook


def shares(parts):
    """TODO 1: parts maps a kind of text to how many characters of it were sent, such as {"system prompt": 400, "tool results": 1200}.
    Return the same keys, each with its share of the total, rounded to 2 places. If the total is 0, every share is 0.
    """
    return None


def cost_per_right(tokens_in, tokens_out, right, prices):
    """TODO 2: What each right answer cost, in dollars. prices is (input, output) per million tokens. If nothing was right, return
    None, because there's no cost per right answer. Round to 6 places.
    """
    return None


def cached_cost(tokens_in, tokens_cached, tokens_out, prices):
    """TODO 3: What one reply cost when some input came from the cache. tokens_in includes the cached tokens. Cached tokens cost a
    tenth of the input price. Round to 6 places.
    """
    return None


class ModelTimer(Hook):
    """TODO 4: The heart of Meter. Record how long each model call took, in seconds, in the list self.seconds. Use self.clock(), which
    returns the time now, in before_model and after_model.
    """

    def __init__(self, clock):
        self.clock = clock
        self.seconds = []


def run_all(make_agent, questions, workers):
    """TODO 5: The heart of run_many. Run each question on a new agent from make_agent(), up to workers at a time, and return each
    run's answer, in the same order as the questions. ThreadPoolExecutor(workers) and its map keep the order for you.
    """
    return None
