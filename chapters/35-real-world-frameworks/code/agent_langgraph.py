"""Chapter 34's coding agent in LangGraph 1.2.20."""
import os

from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from whitebox import load_env
from whitebox.coding import CODING_SYSTEM, coding_tools


def chat_model(spec, max_tokens):
    provider, name = spec.split("/", 1)
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=name, temperature=0.7, num_predict=max_tokens)
    from langchain_google_genai import ChatGoogleGenerativeAI
    load_env()
    return ChatGoogleGenerativeAI(model=name, temperature=0.7, max_output_tokens=max_tokens, google_api_key=os.environ["GEMINI_API_KEY"])


def coding_agent(folder, spec="ollama/qwen2.5:7b", max_tokens=1024):
    tools = [tool.function for tool in coding_tools(folder)]
    model = chat_model(spec, max_tokens).bind_tools(tools)

    def call_model(state: MessagesState):
        return {"messages": [model.invoke([("system", CODING_SYSTEM), *state["messages"]])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(tools, handle_tool_errors=True))  # without it, a tool's error ends the run
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    return graph.compile()


def fix(folder, question, spec="ollama/qwen2.5:7b", max_tokens=1024):
    # A model call and a round of tools are one graph step each, so 15 model calls need 30 steps.
    state = coding_agent(folder, spec, max_tokens).invoke({"messages": [("user", question)]}, {"recursion_limit": 30})
    return state["messages"][-1].content
