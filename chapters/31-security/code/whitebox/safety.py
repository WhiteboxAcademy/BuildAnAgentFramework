"""Limits in code. A model can be fooled, so these limits never ask it."""
import hashlib
import json
from pathlib import Path
from typing import Annotated

from .hooks import Hook
from .tools import tool


def inside(root, path):
    """Return the real location of path, or refuse if it leaves root."""
    root = Path(root).resolve()
    full = (root / path).resolve()
    if not full.is_relative_to(root):
        raise ValueError(f"{path} is outside the folder this tool may use")
    return full


def folder_tools(root):
    """A list_files and a read_file that can't leave root."""

    @tool
    def list_files(folder: Annotated[str, "A folder, such as inbox"] = ".") -> str:
        """List the files in a folder."""
        base = Path(root).resolve()
        full = inside(root, folder)
        if not full.is_dir():
            raise ValueError(f"there is no folder called {folder}")
        return "\n".join(sorted(str(path.relative_to(base)) for path in full.iterdir()))

    @tool
    def read_file(path: Annotated[str, "A path, such as inbox/01-harbour.txt"]) -> str:
        """Read one text file."""
        full = inside(root, path)
        if not full.is_file():
            raise ValueError(f"there is no file called {path}")
        return full.read_text()

    return [list_files, read_file]


class OnlyAllow(Hook):
    """Block a tool unless one argument passes a check you wrote."""

    def __init__(self, name, argument, allowed):
        self.name = name
        self.argument = argument
        self.allowed = allowed

    def before_tool(self, call):
        if call.name != self.name:
            return None
        value = str(call.arguments.get(self.argument, ""))
        return None if self.allowed(value) else f"Error: {self.name} may not use {self.argument} {value}"


class Lockdown(Hook):
    """Once untrusted text has been read, block the tools that act, or ask a person first."""

    def __init__(self, readers, actors, ask=None):
        self.readers = readers
        self.actors = actors
        self.ask = ask
        self.locked = False

    def before_tool(self, call):
        if not self.locked or call.name not in self.actors:
            return None
        if self.ask and self.ask(f"Allow {call.name}({call.arguments})? (y/n) ") == "y":
            return None
        return f"Error: {call.name} is locked, because this run has read untrusted text"

    def after_tool(self, call, output):
        if call.name in self.readers:
            self.locked = True


def fingerprint(tools):
    """A short hash of what these tools say about themselves. If it changes, read them again."""
    described = [[tool.name, tool.description, tool.parameters] for tool in sorted(tools, key=lambda tool: tool.name)]
    return hashlib.sha256(json.dumps(described, sort_keys=True).encode()).hexdigest()[:16]
