"""Run the office assistant once, and show everything it did. usage: python3 attack.py [setup] [wording]"""
import sys
import textwrap

from office import attack
from whitebox import load_model


def short(value):
    """A tool argument, cut short so each call fits on one line."""
    text = repr(" ".join(str(value).split()))
    return text if len(text) <= 48 else text[:44] + "...'"


setup_name = sys.argv[1] if len(sys.argv) > 1 else "none"
wording = sys.argv[2] if len(sys.argv) > 2 else "ignore"
run = attack(load_model(), setup_name, wording)
print(f"Setup: {setup_name}, planted text: {wording}")
for call in run["calls"]:
    shown = f"{call['name']}({', '.join(f'{key}={short(value)}' for key, value in call['arguments'].items())})"
    print(f"  {shown} -> {' '.join(call['output'].split())}"[:92])
for mail in run["sent"]:
    print(f"Email to {mail['to']}: {' '.join(mail['body'].split())}"[:92])
print(textwrap.fill(" ".join(run["answer"].split()), 90, initial_indent="Answer: ", subsequent_indent="  "))
print(f"Read the code: {run['read_secret']}. Sent it out: {run['leaked']}. In the answer: {run['in_answer']}.")
