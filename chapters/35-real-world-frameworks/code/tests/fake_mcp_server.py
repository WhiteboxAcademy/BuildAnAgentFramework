"""A tiny pretend MCP server for the tests, so they need neither the SDK nor a model. Run with new, old, noisy, silent, dies, mute or bare."""
import json
import sys

KIND = sys.argv[1]
TOOLS = [{"name": "double", "description": "Double a number.",
          "inputSchema": {"type": "object", "properties": {"number": {"type": "integer"}}}}]


def answer(message):
    method, params = message["method"], message.get("params", {})
    if method == "server/discover":
        if KIND == "old":
            return {"error": {"code": -32602, "message": "Invalid request parameters"}}
        return {"result": {"supportedVersions": ["2026-07-28"]}}
    if method == "initialize":
        return {"result": {"protocolVersion": "2025-06-18"}}
    if method == "tools/list":
        if KIND == "bare":
            return {"result": {"tools": [{"name": "ping", "description": "Say pong.", "inputSchema": {"type": "object"}}]}}
        return {"result": {"tools": TOOLS}}
    if method == "tools/call" and params["name"] == "double":
        if params["arguments"].get("number") == 0:
            return {"result": {"content": [{"type": "text", "text": "Zero isn't allowed"}], "isError": True}}
        return {"result": {"content": [{"type": "text", "text": str(params["arguments"]["number"] * 2)}], "isError": False}}
    return {"error": {"code": -32601, "message": "Method not found"}}


for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    if KIND == "mute":
        continue
    if KIND == "silent" and message["method"] == "tools/list":
        continue
    if KIND == "dies" and message["method"] == "tools/list":
        sys.exit(1)
    if KIND == "noisy":
        print("debug: got a request", flush=True)
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], **answer(message)}), flush=True)
