"""Hop questions, five runs each: one agent, a relay of two agents, and one agent told to do the same two steps. About 7 minutes."""
from questions import HANDBOOK, strict_pass
from team_setups import Counted, Setups
from whitebox import load_model

FIRST = "\nFind only the first fact you need, and state it in one sentence."
model = Counted(load_model())
setups = Setups(model)
hops = [row for row in HANDBOOK if row[1] == "hop"]


def one_agent(question):
    return setups.one_agent().run(question).answer


def relay(question):
    note = setups.one_agent().run(question + FIRST).answer
    return setups.one_agent().run(f"{question}\nA colleague found: {note}\nFind what's still missing, then answer.").answer


def one_agent_two_steps(question):
    agent = setups.one_agent()
    first = agent.run(question + FIRST)
    return agent.run(f"{question}\nFind what's still missing, then answer.", first.messages).answer


for label, run in (("one agent", one_agent), ("relay of two agents", relay), ("one agent, two steps", one_agent_two_steps)):
    calls = model.calls
    passed = sum(strict_pass(run(row[2]), row[0]) for row in hops for _ in range(5))
    print(f"{label:<22} {passed:>2} of 30   {model.calls - calls} model calls", flush=True)
