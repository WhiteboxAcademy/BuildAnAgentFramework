"""What a model really wrote, before Ollama read it. usage: python3 raw_reply.py MODEL

Ollama turns a model's text into tool calls for us. Here we ask it twice: once through /api/chat, which reads the text, and once through
/api/generate with raw on, which gives the text exactly as the model wrote it. Temperature 0, so each run gives the same reply.
"""
import json
import sys

import requests

from whitebox import AGENT_SYSTEM

URL = "http://127.0.0.1:11434"
model = sys.argv[1]
question = "How much is the till float?"
tool = {"name": "search_handbook", "description": "Search the Quillon Coffee staff handbook.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "What to search for"}}, "required": ["query"]}}
options = {"temperature": 0, "num_predict": 120}

chat = requests.post(f"{URL}/api/chat", timeout=300, json={
    "model": model, "stream": False, "options": options, "tools": [{"type": "function", "function": tool}],
    "messages": [{"role": "system", "content": AGENT_SYSTEM}, {"role": "user", "content": question}]}).json()["message"]
print(f"{model} through /api/chat:")
print(f"  text: {chat.get('content', '')!r}")
print(f"  tool calls: {chat.get('tool_calls')}")

# The same prompt, built by hand from the model's own template (ollama show MODEL --template), sent with raw on.
prompt = ("<|im_start|>system\n" + AGENT_SYSTEM + "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\n"
          "You are provided with function signatures within <tools></tools> XML tags:\n<tools>\n"
          + json.dumps({"type": "function", "function": tool}) + "\n</tools>\n\nFor each function call, return a json object with function "
          "name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{\"name\": <function-name>, \"arguments\": "
          "<args-json-object>}\n</tool_call><|im_end|>\n<|im_start|>user\n" + question + "<|im_end|>\n<|im_start|>assistant\n")
raw = requests.post(f"{URL}/api/generate", timeout=300, json={"model": model, "prompt": prompt, "raw": True, "stream": False,
                                                              "options": options}).json()
print(f"{model} as written:")
for line in raw["response"].split("\n"):
    print(f"  {line}")
