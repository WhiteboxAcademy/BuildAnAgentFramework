"""Questions in one chat, against one chat each. Number the answers, and count how many come back right."""
import random
import re

from questions import HANDBOOK, RECORDS
from team_setups import Counted, Setups
from whitebox import load_model

model = Counted(load_model())
setups = Setups(model)
rows = [row for row in HANDBOOK + RECORDS if row[3]]
random.Random(0).shuffle(rows)


def right(row, answer):
    return any(text.lower() in answer.lower() for text in row[3])


def numbered(text):
    parts = re.split(r"(?m)^\W*(\d+)[.):]", text)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


for size in (10, 20):
    group = rows[:size]
    calls = model.calls
    agent = setups.one_agent()
    agent.max_steps = size + 4
    listing = "\n".join(f"{n}. {row[2]}" for n, row in enumerate(group, 1))
    result = agent.run("Answer every one of these questions. Number each answer to match.\n" + listing)
    replies = numbered(result.answer)
    passed = sum(n in replies and right(row, replies[n]) for n, row in enumerate(group, 1))
    print(f"{size} in one chat:  {passed} of {size} right, {model.calls - calls} model calls")
    print(f"  It said: {' '.join(result.answer.split())[:90]}")

    calls = model.calls
    passed = sum(right(row, setups.one_agent().run(row[2]).answer) for row in group)
    print(f"{size} chats of one: {passed} of {size} right, {model.calls - calls} model calls", flush=True)
