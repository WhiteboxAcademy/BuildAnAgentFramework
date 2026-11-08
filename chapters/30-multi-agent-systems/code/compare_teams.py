"""The same 42 questions, three runs each, on each setup. This takes about 50 minutes. Our results are in results/."""
import time

from questions import HANDBOOK, RECORDS, summary, to_cases
from team_setups import STRICT_MANAGER, Counted, Setups
from whitebox import load_model, run_eval

model = Counted(load_model())
setups = Setups(model)
cases = to_cases(HANDBOOK + RECORDS)

for label, build in (("one agent", setups.one_agent), ("two tools", setups.two_tools), ("router", setups.router),
                     ("manager", setups.manager), ("strict manager", lambda: setups.manager(STRICT_MANAGER))):
    calls, start = model.calls, time.time()
    report = run_eval(build(), cases, runs=3, label=label)
    print(summary(report), flush=True)
    print(f"  {model.calls - calls} model calls, {time.time() - start:.0f} seconds", flush=True)
