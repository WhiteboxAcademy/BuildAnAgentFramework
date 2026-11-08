"""whitebox: an agent framework you can see inside."""
from .agent import Agent, Event, Result
from .messages import Message, ToolCall
from .models import FakeModel, Model, ModelError, OllamaModel, load_model
from .tools import Tool, Toolbox, tool
from .hooks import Approval, Hook, Printer, Tracer, show_trace
from .reliability import Fallback, LoopGuard, RescueToolCalls, Retry, with_timeout
from .evals import (
    Case, Check, Report, compare, contains, excludes, finished, judged, load_report, run_eval, tools_used,
    used_no_tools, used_tool,
)
from .rag import (
    AGENT_SYSTEM, ChromaStore, Chunk, Embedder, FakeEmbedder, Hit, HybridIndex, Index, KeywordIndex, OllamaEmbedder, Rag, Reranker, VectorStore, cosine, excerpts, hit_rate, load_documents, make_chunks, search_tool, split_text,
)
from .context import CutWarning, Summarise, Trim, estimate_tokens, newest, total_tokens
from .memory import Memory
from .planning import Plan, clean
from .durable import Checkpoint, load_messages, once, until_done
from .mcp import McpClient, McpError
from .team import Router, agent_tool
from .safety import Lockdown, OnlyAllow, fingerprint, folder_tools, inside
