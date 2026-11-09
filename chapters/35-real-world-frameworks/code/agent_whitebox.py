"""Chapter 34's coding agent in whitebox, unchanged."""
from whitebox import Agent, RescueToolCalls, Retry, Toolbox, load_model
from whitebox.coding import CODING_SYSTEM, coding_tools


def coding_agent(folder, spec="ollama/qwen2.5:7b", max_tokens=1024):
    model = Retry(RescueToolCalls(load_model(spec)))
    return Agent(model, Toolbox(coding_tools(folder)), system=CODING_SYSTEM, max_steps=15,
                 options={"temperature": 0.7, "num_predict": max_tokens})


def fix(folder, question, spec="ollama/qwen2.5:7b", max_tokens=1024):
    return coding_agent(folder, spec, max_tokens).run(question).answer
