"""Models. The rest of the framework only knows about the Model class."""
import json
import os

import requests

from .messages import Message, ToolCall

DEFAULT_MODEL = "ollama/qwen2.5:7b"
LONGEST_REPLY = 1024  # tokens. A stream that never ends never times out, so a reply needs a limit.


class ModelError(Exception):
    """A model call failed. retryable says whether trying again could help."""

    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.retryable = retryable


class Model:
    """The shape that every model shares."""

    def chat(self, messages, tools=None, **options):
        raise NotImplementedError

    def stream(self, messages, tools=None, **options):
        """Yield the reply's text in pieces, then the finished Message."""
        reply = self.chat(messages, tools, **options)
        if reply.content:
            yield reply.content
        yield reply


class OllamaModel(Model):
    """A model served by Ollama. Translates to and from Ollama's format."""

    def __init__(self, name, url="http://127.0.0.1:11434"):
        self.name = name
        self.url = url

    def to_ollama(self, message):
        data = {"role": message.role, "content": message.content}
        if message.tool_calls:
            data["tool_calls"] = [
                {"function": {"name": call.name, "arguments": call.arguments}}
                for call in message.tool_calls
            ]
        if message.tool_name:
            data["tool_name"] = message.tool_name
        return data

    def tool_to_ollama(self, tool):
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }

    def from_ollama(self, data):
        calls = [
            ToolCall(call["function"]["name"], call["function"]["arguments"])
            for call in data.get("tool_calls") or []
        ]
        return Message(
            "assistant",
            data.get("content", ""),
            calls,
            tokens_in=data.get("prompt_eval_count", 0),
            tokens_out=data.get("eval_count", 0),
        )

    def token_counts(self, data):
        return {key: data[key] for key in ("prompt_eval_count", "eval_count") if key in data}

    def request_body(self, messages, tools, options, stream):
        return {
            "model": self.name,
            "messages": [self.to_ollama(message) for message in messages],
            "tools": [self.tool_to_ollama(tool) for tool in tools or []],
            "stream": stream,
            "options": {"num_predict": LONGEST_REPLY, **options},
        }

    def post(self, body, stream):
        """Send a request, and turn any failure into a ModelError."""
        try:
            response = requests.post(f"{self.url}/api/chat", json=body, timeout=180, stream=stream)
        except requests.RequestException as error:
            raise ModelError(f"Couldn't reach Ollama: {error}", retryable=True) from error
        if not response.ok:
            retryable = response.status_code >= 500
            raise ModelError(f"Ollama said {response.status_code}: {response.text}", retryable)
        return response

    def chat(self, messages, tools=None, **options):
        body = self.request_body(messages, tools, options, stream=False)
        data = self.post(body, stream=False).json()
        return self.from_ollama({**data["message"], **self.token_counts(data)})

    def stream(self, messages, tools=None, **options):
        body = self.request_body(messages, tools, options, stream=True)
        response = self.post(body, stream=True)
        text, calls, counts = "", [], {}
        try:
            for line in response.iter_lines():
                data = json.loads(line)
                if "error" in data:
                    raise ModelError(f"Ollama said: {data['error']}", retryable=True)
                part = data["message"]
                if part.get("content"):
                    text += part["content"]
                    yield part["content"]
                calls += part.get("tool_calls") or []
                counts.update(self.token_counts(data))
        except requests.RequestException as error:
            raise ModelError(f"Lost Ollama partway through a reply: {error}", retryable=True) from error
        yield self.from_ollama({"content": text, "tool_calls": calls, **counts})


class FakeModel(Model):
    """Gives back replies you wrote in advance, and remembers what it was sent."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen = []

    def chat(self, messages, tools=None, **options):
        self.seen.append(list(messages))
        return self.replies.pop(0)


PROVIDERS = {"ollama": OllamaModel}


def load_model(spec=None):
    """Build a model from a "provider/name" string, or from the MODEL setting."""
    spec = spec or os.environ.get("MODEL", DEFAULT_MODEL)
    provider, _, name = spec.partition("/")
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}. Choose from {sorted(PROVIDERS)}.")
    return PROVIDERS[provider](name)
