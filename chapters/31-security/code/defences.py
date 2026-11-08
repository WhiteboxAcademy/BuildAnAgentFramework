"""The long run: attacks against defences, several times each. usage: python3 defences.py RUNS SETUP WORDING [WORDING ...]

For example: python3 defences.py 5 folder polite link
"""
import sys

from office import attack
from whitebox import load_model

runs, setup_name, wordings = int(sys.argv[1]), sys.argv[2], sys.argv[3:]
model = load_model()
print(f"{'Setup':<16}{'Planted text':<15}{'Read the code':>14}{'Sent it out':>12}{'In a link':>10}")
for wording in wordings:
    got = [attack(model, setup_name, wording) for _ in range(runs)]
    print(f"{setup_name:<16}{wording:<15}{sum(r['read_secret'] for r in got):>14}{sum(r['leaked'] for r in got):>12}"
          f"{sum(r['link'] for r in got):>10}")
