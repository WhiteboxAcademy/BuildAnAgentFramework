"""Chapter 35, Part B, the restart fault: kill a whitebox run partway through, start a new process, and see what happens.

    python3 restart_fault.py

A scripted model asks for three side effects, one at a time: append "one", "two" and "three" to a file, then answers. The first
process dies straight after the second append, the way a killed process would, with no chance to tidy up. A second process loads
the checkpoint and carries on. Right is: the file ends with each line once, and the run finishes. It runs twice: with the
Checkpoint alone, and with chapter 27's once() guarding the tool as well. This uses chapter 27's Checkpoint
hook as chapter 34 left it, and runs only for whitebox: LangGraph and Pydantic AI need an extra package to survive a restart.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Annotated

HERE = Path(__file__).parent
from whitebox import Agent, Checkpoint, Message, Model, ToolCall, Toolbox, load_messages, once, tool

WORDS = ["one", "two", "three"]


def build(folder, die_after, guarded):
    log = Path(folder) / "log.txt"

    @tool
    def append(word: Annotated[str, "The word to add"]) -> str:
        """Add a word to the log file."""
        with open(log, "a") as file:
            file.write(word + "\n")
        if word == die_after:
            os._exit(1)  # killed: no saving, no tidying up
        return f"Added {word}."

    class Scripted(Model):
        """Asks for the next word that hasn't had a tool result yet, judged from the conversation alone."""

        def chat(self, messages, tools=None, **options):
            done = sum(1 for m in messages if m.role == "tool")
            if done < len(WORDS):
                return Message("assistant", tool_calls=[ToolCall("append", {"word": WORDS[done]}, id=f"c{done}")])
            return Message("assistant", "All three words are in the log.")

    if guarded:  # chapter 27's once: ask the real file whether this word is already there
        append = once(append, lambda word: log.exists() and word in log.read_text().split())
    state = Path(folder) / "state.json"
    return Agent(Scripted(), Toolbox([append]), system="Test.", hooks=[Checkpoint(state)]), state, log


def child(folder, die_after, guarded):
    agent, state, _ = build(folder, die_after, guarded == "once")
    saved = load_messages(state)
    result = agent.run("Carry on.", saved) if saved else agent.run("Add one, two and three to the log.")
    print(json.dumps({"answer": result.answer, "resumed": saved is not None}))


def main():
    found = []
    for guarded in ("checkpoint", "once"):
        with tempfile.TemporaryDirectory() as folder:
            first = subprocess.run([sys.executable, __file__, "child", folder, "two", guarded], capture_output=True, text=True)
            second = subprocess.run([sys.executable, __file__, "child", folder, "never", guarded], capture_output=True, text=True)
            log = (Path(folder) / "log.txt").read_text().split()
            row = {"framework": "whitebox", "fault": "restart", "setup": guarded, "first_exit": first.returncode,
                   "second_exit": second.returncode, "second_said": second.stdout.strip() or second.stderr.strip()[-300:],
                   "log": log, "each_once": log == WORDS}
            print(json.dumps(row))
            found.append(row)
    out = HERE / "results" / "mine-faults.json"
    rows = [r for r in json.loads(out.read_text()) if r.get("fault") != "restart"] if out.exists() else []
    out.write_text(json.dumps(rows + found, indent=1))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "child":
        child(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        main()
