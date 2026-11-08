"""Chapter 32 exercises, solved."""
from whitebox import ModelError


def gemini_part(message):
    if message.role == "tool":
        return {"role": "user", "parts": [{"functionResponse": {"name": message.tool_name, "response": {"result": message.content}}}]}
    if message.role == "assistant":
        parts = [{"text": message.content}] if message.content else []
        parts += [{"functionCall": {"name": call.name, "args": call.arguments}} for call in message.tool_calls]
        return {"role": "model", "parts": parts}
    return {"role": "user", "parts": [{"text": message.content}]}


def reply_cost(tokens_in, tokens_out, prices):
    price_in, price_out = prices
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 6)


def translate(options, names):
    unknown = [key for key in options if key not in names]
    if unknown:
        raise ValueError(f"Unknown option: {', '.join(unknown)}")
    return {names[key]: value for key, value in options.items()}


def read_env_line(line):
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, _, value = line.partition("=")
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1]
    return key.strip(), value


class Budget:
    def __init__(self, dollars, prices):
        self.dollars = dollars
        self.prices = prices
        self.spent = 0.0

    def charge(self, tokens_in, tokens_out):
        self.spent += reply_cost(tokens_in, tokens_out, self.prices)

    def check(self):
        if self.spent >= self.dollars:
            raise ModelError(f"Stopped: ${self.spent:.4f} spent, and the limit is ${self.dollars:.2f}.", retryable=False)
