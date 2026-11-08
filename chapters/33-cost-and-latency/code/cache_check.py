"""Send the same long prompt five times, and see how much Gemini served from its cache. usage: python3 cache_check.py MODEL

The prompt is the whole handbook, more than 4,096 tokens, which Google's docs give as the least it caches on some models. It costs
under a cent on gemini-3.1-flash-lite.
"""
import sys
import time

from models_setup import build_model, prices_of
from whitebox import Message, load_documents

spec = sys.argv[1]
model = build_model(spec)
handbook = "\n\n".join(load_documents("workspace/handbook").values())
chat = [Message("system", "Answer from this handbook.\n\n" + handbook), Message("user", "How much is the till float? Answer in five words.")]
price_in, price_out = prices_of(spec)
print(f"{'Try':<5}{'Tokens in':>10}{'From cache':>12}{'Cost if none cached':>21}{'Cost':>11}")
for number in range(1, 6):
    reply = model.chat(chat)
    full = (reply.tokens_in * price_in + reply.tokens_out * price_out) / 1_000_000
    paid = ((reply.tokens_in - reply.tokens_cached) * price_in + reply.tokens_cached * price_in / 10 + reply.tokens_out * price_out) / 1_000_000
    print(f"{number:<5}{reply.tokens_in:>10,}{reply.tokens_cached:>12,}{'$' + format(full, '.6f'):>21}{'$' + format(paid, '.6f'):>11}")
    time.sleep(2)
print("Cached input costs a tenth of the normal price on both models here, by Google's pricing page.")
