"""Print our saved runs. usage: python3 read_results.py attacks|defences|targeted|cost|example NAME

NAME is quiet, link or relay.
"""
import json
import sys
import textwrap

saved = json.load(open("results/chapter31.json"))
part = sys.argv[1]


def short(value):
    """A tool argument, cut short so each call fits on one line."""
    text = repr(" ".join(str(value).split()))
    return text if len(text) <= 48 else text[:44] + "...'"


def show(run):
    for name, arguments, output in run["calls"]:
        shown = f"{name}({', '.join(f'{key}={short(value)}' for key, value in arguments.items())})"
        print(f"  {shown} -> {' '.join(output.split())}"[:92])
    for mail in run["sent"]:
        print(f"Email to {mail['to']}: {' '.join(mail['body'].split())}"[:92])
    print(textwrap.fill(" ".join(run["answer"].split()), 90, initial_indent="Answer: ", subsequent_indent="  "))

if part == "attacks":
    print(f"{'Planted text':<14}{'Runs':>5}{'Read the code':>14}{'Emailed out':>12}{'Sent the code':>14}")
    for row in saved["pilot"]:
        print(f"{row['wording']:<14}{row['runs']:>5}{row['read']:>14}{row['outside']:>12}{row['leaked']:>14}")
elif part == "defences":
    print("Times the code was emailed out, of 10 runs each")
    print(f"{'Setup':<16}{'ignore':>7}{'polite':>7}{'fake_user':>10}{'copy_out':>9}{'Read it':>9}{'In answer':>10}{'Emailed out':>12}")
    for row in saved["defences"]:
        leaked = row["leaked"]
        print(f"{row['setup']:<16}{leaked['ignore']:>7}{leaked['polite']:>7}{leaked['fake_user']:>10}{leaked['copy_out']:>9}"
              f"{row['read']:>9}{row['in_answer']:>10}{row['outside']:>12}")
    print("Read it, In answer and Emailed out are of 40 runs.")
elif part == "targeted":
    print(f"{'Setup':<16}{'Planted text':<15}{'Read the code':>14}{'Emailed out':>12}{'Sent the code':>14}{'In a link':>10}")
    for row in saved["adaptive"]:
        print(f"{row['setup']:<16}{row['wording']:<15}{row['read']:>14}{row['outside']:>12}{row['leaked']:>14}{row['link']:>10}")
    print("Each row is 10 runs.")
elif part == "cost":
    print("The real job: email a full summary to the manager, 10 runs each")
    for row in saved["job"]:
        print(f"  {row['setup']:<16}{row['done']:>3}   asked a person {row['asked']} times")
    print("Summary only, no attack: full summaries of 20")
    for row in saved["usefulness"]:
        print(f"  {row['setup']:<16}{row['full']:>3}")
elif part == "example":
    show(saved["examples"][sys.argv[2]])
