"""One question, on any model, with everything it did. usage: python3 one_question.py MODEL [extra]

Add extra to put the one-sentence fix from section 2 in the system prompt.
"""
import sys
import time

from models_setup import STOP_AFTER_CALL, Counted, build_agent, build_model
from whitebox import AGENT_SYSTEM, ModelError

spec = sys.argv[1]
question = "How much is the till float?"
model = Counted(build_model(spec))
agent = build_agent(model, AGENT_SYSTEM + (STOP_AFTER_CALL if "extra" in sys.argv else ""))
started = time.time()
try:
    answer = agent.run(question).answer
except ModelError as error:
    answer = f"ModelError: {error}"
print(f"Model: {spec}")
print(f"Question: {question}")
print(f"Answer: {' '.join(answer.split())[:300]}")
print(f"{model.calls} model calls, {model.tokens_in:,} tokens in, {model.tokens_out:,} out, {time.time() - started:.1f} seconds")
