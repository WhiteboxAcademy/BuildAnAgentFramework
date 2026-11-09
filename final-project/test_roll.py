"""Checks for roll.py. The fixed rolls at the bottom are what the course page must give too."""
import re
from collections import Counter

import pytest

from roll import PROJECTS, now, roll

AT = "2026-11-09T14:32:07Z"


def test_same_inputs_same_project():
    assert roll("Asha Rao", 3, 5, AT) == roll("  asha   RAO ", 3, 5, AT)


def test_dice_change_the_project():
    seen = {roll("Asha Rao", a, b, AT)["number"] for a in range(1, 7) for b in range(1, 7)}
    assert len(seen) > 20


def test_time_changes_the_project():
    seen = {roll("Asha Rao", 3, 5, f"2026-11-09T14:{m:02}:{s:02}Z")["number"] for m in range(2) for s in range(60)}
    assert len(seen) > 40


def test_now_is_a_time_the_roll_takes():
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", now())
    roll("Asha", 1, 1, now())


def test_bad_input():
    for first, second in [(0, 3), (7, 1), (2.5, 3), ("3", 4)]:
        with pytest.raises(ValueError):
            roll("Asha", first, second, AT)
    with pytest.raises(ValueError):
        roll("   ", 1, 1, AT)
    with pytest.raises(ValueError):
        roll("Asha", 1, 1, AT, "expert")
    for at in ["", None, "2026-11-09 14:32:07", "2026-11-09T14:32:07.123Z", "2026-11-09T14:32Z", "2026-11-9T14:32:07Z"]:
        with pytest.raises(ValueError):
            roll("Asha", 1, 1, at)


def test_levels():
    for level in PROJECTS["levels"]:
        pool = {idea["number"] for idea in PROJECTS["ideas"] if idea["level"] == level}
        assert len(pool) >= 10, level
        seen = {roll(f"person {n}", a, b, AT, level)["number"] for n in range(30) for a in range(1, 7) for b in range(1, 7)}
        assert seen == pool, level


def test_spread():
    counts = Counter(roll(f"person {n}", a, b, AT)["number"] for n in range(300) for a in range(1, 7) for b in range(1, 7))
    assert len(counts) == len(PROJECTS["ideas"])
    assert max(counts.values()) < 2 * min(counts.values())


def test_every_idea_is_complete():
    numbers = {twist["number"] for twist in PROJECTS["twists"]}
    for idea in PROJECTS["ideas"]:
        assert idea["harder"] and idea["eval_idea"] and idea["level"] in PROJECTS["levels"], idea["name"]
        assert idea["twists"] and set(idea["twists"]) <= numbers, idea["name"]


# The course page computes the roll in the browser. These must match it exactly.
FIXED = [("Asha Rao", 3, 5, None, 40), ("José", 1, 6, None, 14), ("Zoë Chen", 6, 6, None, 45), ("kushal", 2, 4, None, 5),
         ("Asha Rao", 3, 5, "starter", 27), ("José", 1, 6, "intermediate", 39), ("Zoë Chen", 6, 6, "advanced", 58)]


@pytest.mark.parametrize("name,first,second,level,idea", FIXED)
def test_fixed_rolls(name, first, second, level, idea):
    assert roll(name, first, second, AT, level)["number"] == idea
