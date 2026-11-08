"""Chapter 31 exercises. Complete each TODO, then run: python3 -m pytest test_exercises.py"""
import re  # Provided: you'll need this.
from pathlib import Path  # Provided: you'll need this.
from urllib.parse import urlparse  # Provided: urlparse(url).hostname is the part between :// and the next /.

from whitebox import Hook


def inside_folder(root, path):
    """TODO 1: The heart of folder_tools. Join path onto root, and find where it really leads with Path.resolve(), which
    follows .. and links. Resolve root too. If the result isn't inside root, raise ValueError. Otherwise return it.
    Path.is_relative_to(other) tells you whether one path is inside another.
    """
    return None


def is_quillon_address(text):
    """TODO 2: Return True only if text, once stripped and lower-cased, is exactly one address ending @quillon.example.
    The part before @ may hold letters, digits, dots, underscores, plus signs and hyphens. Use re.fullmatch, so a second
    address or anything else in the text means False.
    """
    return None


def outside_links(answer, domain):
    """TODO 3: Return every link in answer that goes somewhere other than domain or a part of it, in order. A link starts
    with http:// or https:// and runs up to a space, a closing bracket or a closing parenthesis. Its host is allowed if it
    equals domain, or ends with "." + domain. Lower-case the host first.
    """
    return None


class LockAfterReading(Hook):
    """TODO 4: The heart of Lockdown, without the person. After any tool in readers has run, block every tool in actors,
    for the rest of the run. Block a call by returning text that starts with "Error:" from before_tool. Return None to let
    a call run. Remember what happened in after_tool.
    """

    def __init__(self, readers, actors):
        self.readers = readers
        self.actors = actors


def rule_of_two(reads_untrusted, has_private_data, can_act_outside):
    """TODO 5: The chapter's chooser. Each argument is True or False. If at most two are True, return "fine". If all three
    are, the job needs a change: return "remove one, or ask a person".
    """
    return None
