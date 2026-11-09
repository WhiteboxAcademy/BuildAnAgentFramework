"""The framework's own message format. No provider's details belong here."""
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str = ""  # Some providers match each result to its call by id.


@dataclass
class Message:
    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_name: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    tool_id: str = ""
    tokens_cached: int = 0  # input tokens the provider served from its cache, which may cost less
    # What a provider sent, for that provider to read back. Nothing else reads it.
    raw: dict = field(default_factory=dict, repr=False)
