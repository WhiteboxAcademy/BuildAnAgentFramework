"""Fix one bug with one framework, and score it the way chapter 34 does.

    python3 fix_with.py FRAMEWORK BUG [MODEL] [MAX_TOKENS]

FRAMEWORK is whitebox, langgraph or pydantic. BUG is a name from bugs.py or hard_bugs.py. MODEL is ollama/qwen2.5:7b unless you
name another, such as gemini/gemini-3.1-flash-lite. MAX_TOKENS is the most a reply may use, 1024 unless you say.
"""
import importlib
import sys
import tempfile
import time
from pathlib import Path

import bugs
import hard_bugs
from check_bugs import score

QUESTION = "Fix the bug in this project. Start by reading ISSUE.md."
ALL = {bug["name"]: (bug, bugs.make) for bug in bugs.BUGS} | {bug["name"]: (bug, hard_bugs.make) for bug in hard_bugs.BUGS}

if len(sys.argv) < 3 or sys.argv[1] not in ("whitebox", "langgraph", "pydantic") or sys.argv[2] not in ALL:
    sys.exit(f"Usage: python3 fix_with.py whitebox|langgraph|pydantic BUG [MODEL] [MAX_TOKENS]. Bugs: {', '.join(ALL)}")
framework = importlib.import_module(f"agent_{sys.argv[1]}")
bug, make = ALL[sys.argv[2]]
spec = sys.argv[3] if len(sys.argv) > 3 else "ollama/qwen2.5:7b"
max_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 1024

with tempfile.TemporaryDirectory() as tmp:
    folder = make(bug, Path(tmp) / bug["name"])
    start = time.monotonic()
    answer = framework.fix(folder, QUESTION, spec, max_tokens)
    seconds = time.monotonic() - start
    visible, hidden = score(bug, folder)
print(f"{sys.argv[1]} on {spec}, {seconds:.0f} s: {' '.join(str(answer).split())[:300]}")
print(f"Original tests pass: {visible}. Hidden tests pass: {hidden}. Fixed: {visible and hidden}.")
