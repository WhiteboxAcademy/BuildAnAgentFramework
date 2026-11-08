"""What GeminiModel sends for a short chat with one tool call. Nothing is sent: we only build the request. No key or network needed."""
import json
from typing import Annotated

from whitebox import GeminiModel, Message, ToolCall, tool


@tool
def get_rota(day: Annotated[str, "A day, such as Friday"]) -> str:
    """Get who opens the shop on one day."""
    return "Ana opens."


chat = [
    Message("system", "You help Quillon Coffee staff."),
    Message("user", "Who opens on Friday?"),
    Message("assistant", "", [ToolCall("get_rota", {"day": "Friday"}, "call-1")]),
    Message("tool", "Ana opens.", tool_name="get_rota", tool_id="call-1"),
]
body = GeminiModel("gemini-3.1-flash-lite", key="not-a-real-key-demo-only").request_body(chat, [get_rota], {"temperature": 0.7})
print("systemInstruction:", json.dumps(body["systemInstruction"]))
print("contents:")
for item in body["contents"]:
    print(" ", json.dumps(item))
print("tools:", [declared["name"] for declared in body["tools"][0]["functionDeclarations"]])
print("generationConfig:", json.dumps(body["generationConfig"]))
