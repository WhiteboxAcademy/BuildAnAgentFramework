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


def load_env(start="."):
    """Read KEY=value lines from the nearest .env file, in this folder or a folder above. Settings already made win."""
    folder = os.path.abspath(start)
    while True:
        path = os.path.join(folder, ".env")
        if os.path.isfile(path):
            break
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        folder = parent
    with open(path) as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return path


class GeminiModel(Model):
    """A Gemini model, over Google's generateContent REST API. Translates to and from Gemini's format."""

    URL = "https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent"
    OPTIONS = {"temperature": "temperature", "num_predict": "maxOutputTokens"}

    def __init__(self, name, key=None):
        self.name = name
        self.key = key or os.environ.get("GEMINI_API_KEY", "")
        if not self.key:
            raise ModelError("No GEMINI_API_KEY. Copy .env.example to .env, and put your key there.")

    def to_gemini(self, messages):
        """Gemini wants the system prompt apart, roles user and model, and tool results as user parts."""
        system = [message.content for message in messages if message.role == "system"]
        contents = []
        for message in messages:
            if message.role == "system":
                continue
            if message.role == "tool":
                part = {"functionResponse": {"name": message.tool_name, "response": {"result": message.content}}}
                if message.tool_id:
                    part["functionResponse"]["id"] = message.tool_id
                if contents and contents[-1]["role"] == "user" and "functionResponse" in contents[-1]["parts"][0]:
                    contents[-1]["parts"].append(part)  # results of calls made together go back together
                else:
                    contents.append({"role": "user", "parts": [part]})
            elif message.role == "assistant":
                contents.append({"role": "model", "parts": message.raw.get("gemini_parts") or self.parts_of(message)})
            else:
                contents.append({"role": "user", "parts": [{"text": message.content}]})
        body = {"contents": contents}
        if system:
            body["systemInstruction"] = {"parts": [{"text": "\n\n".join(system)}]}
        return body

    def parts_of(self, message):
        """Parts for a reply Gemini didn't write, such as one from another model."""
        parts = [{"text": message.content}] if message.content else []
        for call in message.tool_calls:
            parts.append({"functionCall": {"name": call.name, "args": call.arguments} | ({"id": call.id} if call.id else {})})
        return parts

    def config(self, options):
        unknown = [key for key in options if key not in self.OPTIONS and key != "thinking"]
        if unknown:
            known = ", ".join([*self.OPTIONS, "thinking"])
            raise ValueError(f"GeminiModel doesn't know the option {', '.join(unknown)}. It knows {known}.")
        config = {self.OPTIONS[key]: value for key, value in options.items() if key in self.OPTIONS}
        if "thinking" in options:
            config["thinkingConfig"] = {"thinkingLevel": options["thinking"].upper()}
        return config

    def request_body(self, messages, tools, options):
        body = self.to_gemini(messages)
        if tools:
            body["tools"] = [{"functionDeclarations": [
                {"name": tool.name, "description": tool.description, "parameters": tool.parameters} for tool in tools]}]
        config = self.config(options)
        if config:
            body["generationConfig"] = config
        return body

    def from_gemini(self, data):
        candidate = (data.get("candidates") or [{}])[0]
        parts = candidate.get("content", {}).get("parts")
        if parts is None:
            reason = candidate.get("finishReason") or data.get("promptFeedback", {}).get("blockReason", "no reason given")
            raise ModelError(f"Gemini sent no reply: {reason}", retryable=False)
        text = "".join(part.get("text", "") for part in parts if not part.get("thought"))
        calls = [ToolCall(part["functionCall"]["name"], part["functionCall"].get("args", {}), part["functionCall"].get("id", ""))
                 for part in parts if "functionCall" in part]
        usage = data.get("usageMetadata", {})
        return Message("assistant", text, calls, tokens_in=usage.get("promptTokenCount", 0),
                       tokens_out=usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0),
                       raw={"gemini_parts": parts})

    def chat(self, messages, tools=None, **options):
        body = self.request_body(messages, tools, options)
        try:
            response = requests.post(self.URL.format(name=self.name), json=body, timeout=180,
                                     headers={"x-goog-api-key": self.key})  # in a header, never in the address
        except requests.RequestException as error:
            raise ModelError(f"Couldn't reach Gemini: {type(error).__name__}", retryable=True) from None
        if not response.ok:
            try:
                said = response.json()["error"]["message"]
            except (ValueError, KeyError, TypeError):
                said = response.text[:300]
            raise ModelError(f"Gemini said {response.status_code}: {said}", retryable=response.status_code in (429, 500, 503))
        return self.from_gemini(response.json())


class FakeModel(Model):
    """Gives back replies you wrote in advance, and remembers what it was sent."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen = []

    def chat(self, messages, tools=None, **options):
        self.seen.append(list(messages))
        return self.replies.pop(0)


PROVIDERS = {"ollama": OllamaModel, "gemini": GeminiModel}


def load_model(spec=None):
    """Build a model from a "provider/name" string, or from the MODEL setting."""
    load_env()
    spec = spec or os.environ.get("MODEL", DEFAULT_MODEL)
    provider, _, name = spec.partition("/")
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}. Choose from {sorted(PROVIDERS)}.")
    return PROVIDERS[provider](name)
