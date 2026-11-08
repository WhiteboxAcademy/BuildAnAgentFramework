"""The 42 questions, several at a time. usage: python3 many_at_once.py MODEL WORKERS

Each question gets its own new agent, because hooks such as LoopGuard keep state from one run to the next.
On qwen2.5:7b one pass takes about 2.5 minutes. On gemini-3.1-flash-lite one pass cost us about two cents.
"""
import sys
import time

from models_setup import build_agent, build_model
from questions import HANDBOOK, RECORDS, to_cases
from whitebox import run_many

spec, workers = sys.argv[1], int(sys.argv[2])
model = build_model(spec)
cases = to_cases(HANDBOOK + RECORDS)
started = time.time()
results = run_many(lambda: build_agent(model), [case.question for case in cases], workers)
passed = sum(all(check.test(result) for check in case.checks) for case, result in zip(cases, results))
print(f"{spec}, {workers} at a time: {passed} of {len(cases)} right, in {time.time() - started:.0f} seconds")
