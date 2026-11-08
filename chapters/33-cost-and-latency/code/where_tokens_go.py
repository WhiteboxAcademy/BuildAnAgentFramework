"""What each model call sends, split into its parts. usage: python3 where_tokens_go.py MODEL"""
import sys

from models_setup import build_agent, build_model
from whitebox import Hook, where_tokens_go


class Keep(Hook):
    """Keeps a copy of what each model call was sent."""

    def __init__(self):
        self.sent = []

    def before_model(self, messages):
        self.sent.append(list(messages))


keep = Keep()
agent = build_agent(build_model(sys.argv[1]), hooks=[keep])
agent.run("Which branch had a flood, and what did it cost?")
names = list(where_tokens_go([]))
print(f"{'Call':<6}" + "".join(f"{name:>18}" for name in names))
totals = dict.fromkeys(names, 0)
for number, messages in enumerate(keep.sent, 1):
    parts = where_tokens_go(messages, agent.toolbox.describe())
    print(f"{number:<6}" + "".join(f"{parts[name]:>18,}" for name in names))
    for name in names:
        totals[name] += parts[name]
everything = sum(totals.values())
print(f"{'Share':<6}" + "".join(f"{totals[name] / everything:>18.0%}" for name in names))
print("Characters, not tokens. A token is about four characters of English.")
