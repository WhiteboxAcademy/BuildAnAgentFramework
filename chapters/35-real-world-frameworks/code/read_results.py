"""Provided: print our saved runs from results/chapter35.json, so you can see every table without running anything.

    python3 read_results.py scores | faults | note | 14b | tune
"""
import json
import sys
from pathlib import Path

DATA = json.loads((Path(__file__).parent / "results" / "chapter35.json").read_text())
SETS = DATA["sets"]
FRAMEWORKS = ["whitebox", "langgraph", "pydantic"]
NAMES = {"whitebox": "whitebox", "langgraph": "LangGraph", "pydantic": "Pydantic AI"}


def fixed(runs):
    return sum(r["visible"] and r["hidden"] for r in runs)


def cell(key):
    runs = SETS.get(key)
    return f"{fixed(runs)}/{len(runs)}" if runs else "-"


def scores():
    print("Fixed means the original tests and the hidden tests pass. Hard: 10 bugs. Easy: chapter 34's 20.")
    print(f"{'Model, bugs':<28}" + "".join(f"{NAMES[f]:>13}" for f in FRAMEWORKS))
    for model, bugs, label in [("gemini-3.1-flash-lite", "hard", "Flash-Lite, hard, once"),
                               ("qwen2.5:7b", "hard", "7B, hard, 3 times"), ("qwen2.5:7b", "easy", "7B, easy, 3 times")]:
        print(f"{label:<28}" + "".join(f"{cell(f'{f}/{model}/{bugs}'):>13}" for f in FRAMEWORKS))
    missed = {f: sorted({r["bug"] for r in SETS[f"{f}/gemini-3.1-flash-lite/hard"] if not (r["visible"] and r["hidden"])})
              for f in FRAMEWORKS}
    print("Missed on Flash-Lite: " + ", ".join(f"{NAMES[f]} {' '.join(m)}" for f, m in missed.items()))


VERDICTS = {
    "wrong_type": ("A wrong-type argument", lambda r: "broke: tool ran with it" if r["tools_ran"] else "caught"),
    "empty_reply": ("An empty reply", lambda r: "broke: took it as answer" if r.get("answer") == "" else "recovered"),
    "same_call": ("The same call 30 times", lambda r: f"stopped, tool ran {len(r['tools_ran'])}x" if not r["error"]
                  else f"raised, tool ran {len(r['tools_ran'])}x"),
    "tool_error": ("A tool raises an error", lambda r: "crashed" if r["error"] else "recovered"),
    "budget": ("A token budget", lambda r: ("no budget: ran on" if not r["error"] else "stopped by raising")),
    "model_error": ("A model call fails once", lambda r: "crashed" if r["error"] else "recovered"),
    "cut_off": ("A reply cut off", lambda r: "took it as the answer"),
}


def faults():
    rows = {(r["fault"], r["framework"]): r for r in DATA["faults"] if r["fault"] != "restart"}
    print("A scripted model plays the same fault in every framework, each at its defaults.")
    print((f"{'Fault':<25}" + "".join(f"{NAMES[f]:<26}" for f in FRAMEWORKS)).rstrip())
    for fault, (label, verdict) in VERDICTS.items():
        print((f"{label:<25}" + "".join(f"{verdict(rows[(fault, f)]):<26}" for f in FRAMEWORKS)).rstrip())
    restart = {r["setup"]: r for r in DATA["faults"] if r["fault"] == "restart"}
    print(f"{'A restart mid-run':<25}" + f"{'resumed; ' + ('each step once' if restart['checkpoint']['each_once'] else 'repeated a step'):<26}"
          + f"{'needs another package':<26}" + "needs another package")
    print(f"With chapter 27's once(), whitebox's restart ran each step once: {restart['once']['each_once']}.")


def note():
    print("What Pydantic AI sent qwen2.5 before our question:")
    for message in DATA["first_request_with_note"]:
        text = message["content"]
        print(f"  {message['role']:<7}{text[:78] + '...' if len(text) > 78 else text}")
    print("\nqwen2.5:14b's first reply, in each run of our logged rerun with that note:")
    for reply in DATA["pydantic_first_replies_with_note"]:
        text = " ".join(reply.split())
        print("  " + (text[:81] + "..." if len(text) > 81 else text))


def fourteen():
    print("qwen2.5:14b, hard bugs, once each")
    print(f"{'Framework':<30}{'Fixed':>7}{'Read ISSUE.md first':>21}{'Crashed':>9}")
    for key, label in [("whitebox/qwen2.5:14b/hard", "whitebox"), ("langgraph/qwen2.5:14b/hard", "LangGraph"),
                       ("pydantic/qwen2.5:14b/hard/with-note-first", "Pydantic AI, with its note"),
                       ("pydantic/qwen2.5:14b/hard/with-note-logged", "Pydantic AI, with it again"),
                       ("pydantic/qwen2.5:14b/hard", "Pydantic AI, note left out")]:
        runs = SETS[key]
        first = sum(r["first_file"] == "ISSUE.md" for r in runs)
        crashed = sum(bool(r["error"]) for r in runs)
        print(f"{label:<30}{fixed(runs):>4}/{len(runs):<3}{first:>15}/{len(runs):<5}{crashed:>7}")
    errors = {r["error"][:70] for r in SETS["langgraph/qwen2.5:14b/hard"] if r["error"]}
    print("LangGraph's crashes: " + "; ".join(errors))


def tune():
    print("gemini-3.6-flash, whitebox, hard bugs, once each")
    print(f"{'Most tokens a reply may use':<30}{'Fixed':>7}{'No reply at all':>17}{'Cost':>9}")
    for cap in ("1024", "8192"):
        runs = SETS[f"whitebox/gemini-3.6-flash/hard/cap{cap}"]
        empty = sum("MAX_TOKENS" in (r["error"] or "") for r in runs)
        cost = sum(r["dollars"] or 0 for r in runs)
        print(f"{cap:<30}{fixed(runs):>4}/{len(runs):<3}{empty:>13}{cost:>12.3f}")
    print("Changed the tests at 8192: "
          f"{sum(r['tests_changed'] for r in SETS['whitebox/gemini-3.6-flash/hard/cap8192'])} runs, every one by adding tests.")


COMMANDS = {"scores": scores, "faults": faults, "note": note, "14b": fourteen, "tune": tune}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"Usage: python3 read_results.py {' | '.join(COMMANDS)}")
    COMMANDS[sys.argv[1]]()
