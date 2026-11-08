"""The 42 questions on any model. usage: python3 run_eval.py MODEL [RUNS] [extra]

Our results are in results/. On qwen2.5:7b three runs take about 7 minutes. On gemini-3.1-flash-lite one run cost us about $0.02.
"""
import sys
import time

from models_setup import STOP_AFTER_CALL, Counted, build_agent, build_model
from questions import HANDBOOK, RECORDS, summary, to_cases
from whitebox import AGENT_SYSTEM, run_eval

spec = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1
model = Counted(build_model(spec))
agent = build_agent(model, AGENT_SYSTEM + (STOP_AFTER_CALL if "extra" in sys.argv else ""))
started = time.time()
report = run_eval(agent, to_cases(HANDBOOK + RECORDS), runs=runs, label=spec.split("/", 1)[1])
print(summary(report))
print(f"  {model.calls} model calls, {model.tokens_in:,} tokens in, {time.time() - started:.0f} seconds")
