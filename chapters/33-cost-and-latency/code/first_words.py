"""How long until the first words arrive, and until the whole reply has. usage: python3 first_words.py MODEL"""
import sys
import time

from models_setup import build_model
from whitebox import Message

model = build_model(sys.argv[1])
question = [Message("user", "In three short sentences, why should a cafe count its till float at the start of a shift?")]
print(f"{'Try':<5}{'First words':>12}{'Whole reply':>13}")
for number in range(1, 4):
    started = time.perf_counter()
    first = None
    for piece in model.stream(question):
        if first is None and not isinstance(piece, Message) and piece.strip():
            first = time.perf_counter() - started
    whole = time.perf_counter() - started
    print(f"{number:<5}{first or whole:>11.2f}s{whole:>12.2f}s")
