"""Chapter 33 exercises, solved."""
from concurrent.futures import ThreadPoolExecutor

from whitebox import Hook


def shares(parts):
    total = sum(parts.values())
    return {name: round(count / total, 2) if total else 0 for name, count in parts.items()}


def cost_per_right(tokens_in, tokens_out, right, prices):
    if not right:
        return None
    price_in, price_out = prices
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000 / right, 6)


def cached_cost(tokens_in, tokens_cached, tokens_out, prices):
    price_in, price_out = prices
    return round(((tokens_in - tokens_cached) * price_in + tokens_cached * price_in / 10 + tokens_out * price_out) / 1_000_000, 6)


class ModelTimer(Hook):
    def __init__(self, clock):
        self.clock = clock
        self.seconds = []

    def before_model(self, messages):
        self.started = self.clock()

    def after_model(self, reply):
        self.seconds.append(self.clock() - self.started)


def run_all(make_agent, questions, workers):
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(lambda question: make_agent().run(question).answer, questions))
