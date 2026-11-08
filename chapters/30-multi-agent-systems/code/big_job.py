"""How many dairy deliveries were late in 2025? 48 logs, about 60,000 tokens, far too much for one call."""
import re

from library import OPTIONS
from whitebox import Message, load_documents, load_model

BRANCHES = ["harbour", "old-mill", "riverside", "station"]
ASK = "Copy every sentence that says a delivery was late, one per line. If there are none, reply: none"


def copied(reply, log):
    """Count only the lines that really appear in the log, so a stray line can't add to the total."""
    lines = [re.sub(r"^[\s*\-\d.)]+", "", line).strip() for line in reply.splitlines()]
    return sum(bool(line) and line.lower() != "none" and line.lower() in log.lower() for line in lines)


model = load_model()
logs = {name: text for name, text in load_documents("workspace/records").items() if name.startswith("log-")}


def of(branch):
    return [text for name, text in sorted(logs.items()) if name.startswith(f"log-{branch}")]


print(f"{len(logs)} logs, {sum(map(len, logs.values())):,} characters\n")
print(f"{'Branch':<11}{'Exact pattern':>14}{'Word delivery':>14}{'Team of 12':>12}")
for branch in BRANCHES:
    exact = sum(len(re.findall(r"Dairy delivery was \d+ minutes late", text)) for text in of(branch))
    word = sum(len(re.findall(r"(?i)delivery", text)) for text in of(branch))
    team = sum(copied(model.chat([Message("user", f"{text}\n\n{ASK}")], **OPTIONS).content, text) for text in of(branch))
    print(f"{branch:<11}{exact:>14}{word:>14}{team:>12}", flush=True)
