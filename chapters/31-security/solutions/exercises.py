"""Chapter 31 exercises, solved."""
import re
from pathlib import Path
from urllib.parse import urlparse

from whitebox import Hook


def inside_folder(root, path):
    root = Path(root).resolve()
    full = (root / path).resolve()
    if not full.is_relative_to(root):
        raise ValueError(f"{path} is outside {root}")
    return full


def is_quillon_address(text):
    return re.fullmatch(r"[a-z0-9._+-]+@quillon\.example", text.strip().lower()) is not None


def outside_links(answer, domain):
    found = []
    for link in re.findall(r"https?://[^\s)\]]+", answer):
        host = (urlparse(link).hostname or "").lower()
        if host != domain and not host.endswith("." + domain):
            found.append(link)
    return found


class LockAfterReading(Hook):
    def __init__(self, readers, actors):
        self.readers = readers
        self.actors = actors
        self.locked = False

    def before_tool(self, call):
        if self.locked and call.name in self.actors:
            return f"Error: {call.name} is locked after reading untrusted text"
        return None

    def after_tool(self, call, output):
        if call.name in self.readers:
            self.locked = True


def rule_of_two(reads_untrusted, has_private_data, can_act_outside):
    if reads_untrusted and has_private_data and can_act_outside:
        return "remove one, or ask a person"
    return "fine"
