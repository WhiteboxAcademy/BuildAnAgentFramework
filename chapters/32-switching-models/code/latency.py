"""How long one tiny reply takes, on each model. usage: python3 latency.py [TIMES]   It costs well under a cent."""
import sys
import time

from models_setup import build_model
from whitebox import Message, ModelError

times = int(sys.argv[1]) if len(sys.argv) > 1 else 3
print(f"{'Model':<32}{'Seconds for each try':<30}")
for spec in ["ollama/qwen2.5:7b", "gemini/gemini-3.1-flash-lite", "gemini/gemini-3.6-flash", "gemini/gemini-3.8-flash"]:
    model, took = build_model(spec), []
    for _ in range(times):
        started = time.time()
        try:
            model.chat([Message("user", "Reply with: ok")])
            took.append(f"{time.time() - started:.1f}")
        except ModelError as error:
            took.append(f"failed ({str(error)[:40]})")
    print(f"{spec:<32}{'  '.join(took)}", flush=True)
