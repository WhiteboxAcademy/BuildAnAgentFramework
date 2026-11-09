"""Chapter 35, Part B: the same faults, played by a scripted model, in whitebox, LangGraph and Pydantic AI.

    python3 faults.py

No real model is used, so it's free and every run is the same. Each framework is used as released, with its defaults: no tool
error handling or limits added beyond what's named in the fault. Each fault records what happened, as raw facts: whether the run
finished, crashed or was stopped, what the tool was called with, and what the model was shown next. Results go to
results/mine-faults.json.
"""
import json
import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
HERE = Path(__file__).parent
from typing import Annotated

ran = []  # every real tool call, as (tool, arguments)


def double(days: Annotated[int, "A number of days"]) -> str:
    """Double a number of days.

    Args:
        days: A number of days
    """
    ran.append(("double", days))
    return f"{days * 2}"


def flaky() -> str:
    """Read today's orders."""
    ran.append(("flaky", None))
    raise RuntimeError("the orders database is down")


def lookup(word: Annotated[str, "A word to look up"]) -> str:
    """Look up a word.

    Args:
        word: A word to look up
    """
    ran.append(("lookup", word))
    return f"{word}: nothing found"


TOOLS = [double, flaky, lookup]

# A script is a list of steps. ("call", name, arguments) asks for a tool; ("text", words) is a reply with no tool call.
FAULTS = {
    "wrong_type": [("call", "double", {"days": "three"}), ("text", "Done.")],
    "empty_reply": [("text", ""), ("text", "The answer is 42.")],
    "same_call": [("call", "lookup", {"word": "x"})] * 30 + [("text", "Done.")],
    "tool_error": [("call", "flaky", {}), ("text", "Done.")],
    "budget": [("call", "lookup", {"word": f"w{i}"}) for i in range(10)] + [("text", "Done.")],
    # The reply stops at the token limit mid-sentence, as Flash 3.6's did when thinking filled the cap.
    # The model call itself fails once, as Ollama's "prediction aborted, token repeat limit reached" did on 14B.
    "model_error": [("raise", "prediction aborted, token repeat limit reached"), ("text", "The answer is 42.")],
    "cut_off": [("cut", "The fix is to change the loop so that ? Wait! Let's check"), ("text", "The answer is 42.")],
}
TOKENS_PER_REPLY = 100  # each scripted reply claims 100 tokens in and 10 out
BUDGET_TOKENS = 450     # the budget fault's limit: crossed during the fifth reply
STEPS = 15


class Script:
    """Hands out the steps in order and remembers what the model was shown each time."""

    def __init__(self, steps):
        self.steps, self.shown = list(steps), []

    def next(self, last_message):
        self.shown.append(last_message)
        return self.steps.pop(0) if self.steps else ("text", "(script ran out)")


# whitebox ------------------------------------------------------------------------------------------------------------------------

def run_whitebox(fault, script):
    from whitebox import Agent, LoopGuard, Message, Model, ModelError, RescueToolCalls, Retry, SpendLimit, ToolCall, Toolbox, tool

    class Scripted(Model):
        def chat(self, messages, tools=None, **options):
            step = script.next(messages[-1].content)
            if step[0] == "raise":  # whitebox's Ollama model reports this error as worth retrying
                raise ModelError(f"Ollama said: {step[1]}", retryable=True)
            calls = [ToolCall(step[1], step[2], id=f"c{len(script.shown)}")] if step[0] == "call" else []
            # whitebox's Message has no field for why a reply stopped, so a cut-off reply is just its text.
            return Message("assistant", "" if calls else step[1], tool_calls=calls, tokens_in=TOKENS_PER_REPLY, tokens_out=10)

    model = Scripted()
    if fault == "budget":
        # SpendLimit counts dollars, so a price of $1 per million tokens makes the limit a token count.
        model = SpendLimit(model, BUDGET_TOKENS / 1_000_000, (1.0, 1.0))
    # The course's usual setup: Retry, RescueToolCalls and LoopGuard.
    agent = Agent(Retry(RescueToolCalls(model)), Toolbox([tool(f) for f in TOOLS]), system="Test.", max_steps=STEPS,
                  hooks=[LoopGuard()])
    result = agent.run("Go.")
    return {"answer": result.answer, "stopped": result.stopped}


# LangGraph -----------------------------------------------------------------------------------------------------------------------

def run_langgraph(fault, script):
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langgraph.graph import START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition

    class Scripted(BaseChatModel):
        @property
        def _llm_type(self):
            return "scripted"

        def bind_tools(self, tools, **kwargs):
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            step = script.next(str(messages[-1].content))
            if step[0] == "raise":
                raise RuntimeError(step[1])
            calls = [{"name": step[1], "args": step[2], "id": f"c{len(script.shown)}"}] if step[0] == "call" else []
            message = AIMessage(content="" if calls else step[1], tool_calls=calls,
                                response_metadata={"finish_reason": "length" if step[0] == "cut" else "stop"},
                                usage_metadata={"input_tokens": TOKENS_PER_REPLY, "output_tokens": 10,
                                                "total_tokens": TOKENS_PER_REPLY + 10})
            return ChatResult(generations=[ChatGeneration(message=message)])

    model = Scripted().bind_tools(TOOLS)
    graph = StateGraph(MessagesState)
    graph.add_node("model", lambda state: {"messages": [model.invoke(state["messages"])]})
    graph.add_node("tools", ToolNode(TOOLS))  # the default error handling
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    # LangGraph has no token budget of its own; recursion_limit counts graph steps, not tokens.
    messages = graph.compile().invoke({"messages": [("user", "Go.")]}, {"recursion_limit": 2 * STEPS})["messages"]
    return {"answer": messages[-1].content, "stopped": False}


# Pydantic AI ---------------------------------------------------------------------------------------------------------------------

def run_pydantic(fault, script):
    from pydantic_ai import Agent, UsageLimits
    from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
    from pydantic_ai.models.function import FunctionModel
    from pydantic_ai.usage import RequestUsage

    def scripted(messages, info):
        last = messages[-1].parts[-1]
        step = script.next(str(getattr(last, "content", last)))
        if step[0] == "raise":
            raise RuntimeError(step[1])
        part = ToolCallPart(step[1], step[2], tool_call_id=f"c{len(script.shown)}") if step[0] == "call" else TextPart(step[1])
        return ModelResponse(parts=[part], usage=RequestUsage(input_tokens=TOKENS_PER_REPLY, output_tokens=10),
                             finish_reason="length" if step[0] == "cut" else "stop")

    agent = Agent(FunctionModel(scripted), system_prompt="Test.", tools=TOOLS)
    limits = UsageLimits(request_limit=STEPS)
    if fault == "budget":
        limits = UsageLimits(request_limit=STEPS, total_tokens_limit=BUDGET_TOKENS)
    return {"answer": agent.run_sync("Go.", usage_limits=limits).output, "stopped": False}


RUNNERS = {"whitebox": run_whitebox, "langgraph": run_langgraph, "pydantic": run_pydantic}


def main():
    only = sys.argv[1:]
    rows = []
    for fault, steps in FAULTS.items():
        if only and fault not in only:
            continue
        for framework, runner in RUNNERS.items():
            ran.clear()
            script = Script(steps)
            try:
                outcome, error = runner(fault, script), None
            except Exception as e:
                outcome, error = {}, f"{type(e).__name__}: {e}"[:300]
            row = {"fault": fault, "framework": framework, "error": error, "model_replies": len(script.shown),
                   "tools_ran": [list(map(str, r)) for r in ran], "shown_after_first": script.shown[1:3]} | outcome
            rows.append(row)
            print(json.dumps(row)[:400], flush=True)
    out = HERE / "results" / "mine-faults.json"
    kept = [r for r in json.loads(out.read_text()) if r["fault"] not in {row["fault"] for row in rows}] if out.exists() else []
    out.write_text(json.dumps(kept + rows, indent=1))


if __name__ == "__main__":
    main()
