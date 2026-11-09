"""Roll for your final project: your name, the time and two dice give one idea, with a harder version and the twists that fit it.

    python3 roll.py "Your Name" 3 5
    python3 roll.py "Your Name" 3 5 starter        # or intermediate, or advanced
    python3 roll.py "Your Name" 3 5 starter --at 2026-11-09T14:32:07Z

The time makes each roll different, even with the same dice. The roll prints the time it used, to the second, and `--at` with that
time gives the same project again, here and on the course page. Nothing is sent anywhere.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECTS = json.loads((Path(__file__).parent / "projects.json").read_text(encoding="utf-8"))
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def now():
    """The time now in UTC, to the second, as the roll uses it: 2026-11-09T14:32:07Z."""
    return datetime.now(timezone.utc).strftime(TIME_FORMAT)


def roll(name, first, second, at, level=None, projects=PROJECTS):
    """Return the idea for a name, two dice, a UTC time and, if you like, a level. The name is lower-cased and its spaces tidied,
    so "Asha  Rao" and "asha rao" roll the same. The first 4 bytes of a SHA-256 hash pick the idea, from the ideas at that level or
    from all."""
    if level is not None and level not in projects["levels"]:
        raise ValueError(f"the level is one of: {', '.join(projects['levels'])}")
    if not all(isinstance(die, int) and 1 <= die <= 6 for die in (first, second)):
        raise ValueError("each die is a whole number from 1 to 6")
    try:
        if datetime.strptime(at, TIME_FORMAT).strftime(TIME_FORMAT) != at:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("the time is UTC, to the second, like 2026-11-09T14:32:07Z") from None
    name = " ".join(name.lower().split())
    if not name:
        raise ValueError("type your name")
    digest = hashlib.sha256(f"{name}|{at}|{first}|{second}".encode("utf-8")).digest()
    ideas = [idea for idea in projects["ideas"] if level in (None, idea["level"])]
    return ideas[int.from_bytes(digest[:4], "big") % len(ideas)]


if __name__ == "__main__":
    args = sys.argv[1:]
    at = now()
    if "--at" in args:
        i = args.index("--at")
        at = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
    if len(args) not in (3, 4):
        sys.exit('Usage: python3 roll.py "Your Name" FIRST_DIE SECOND_DIE [starter|intermediate|advanced] [--at TIME]')
    level = args[3] if len(args) == 4 else None
    try:
        idea = roll(args[0], int(args[1]), int(args[2]), at, level)
    except ValueError as error:
        sys.exit(f"Can't roll: {error}.")
    print(f"Idea {idea['number']}: {idea['name']} ({idea['level']})")
    print(f"  {idea['what']}")
    print(f"  Builds on: {idea['builds_on']}. Your eval could check: {idea['eval_idea']}")
    print(f"  Harder version: {idea['harder']}")
    print("Twists that fit it, if you want one:")
    for twist in PROJECTS["twists"]:
        if twist["number"] in idea["twists"]:
            print(f"  {twist['number']}. {twist['twist']}")
    print(f"\nThe rules: {PROJECTS['rules']}")
    again = f'python3 roll.py "{args[0]}" {args[1]} {args[2]}' + (f" {level}" if level else "") + f" --at {at}"
    print(f"\nRolled at {at}. To see this roll again: {again}")
