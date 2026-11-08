"""Memory: facts about a person that survive after the conversation ends."""
import json
import os
from datetime import date
from pathlib import Path
from typing import Annotated

from .hooks import Hook
from .tools import tool


class Memory(Hook):
    """Notes in a JSON file, oldest first. The model says when to save. The code keeps the user's own words."""

    def __init__(self, path, today=date.today):
        self.path = Path(path)
        self.today = today
        self.latest = ""
        self.notes = json.loads(self.path.read_text()) if self.path.exists() else []

    def before_model(self, messages):
        """Remember what the user just said, so the tool can save their words and not the model's."""
        said = [message.content for message in messages if message.role == "user"]
        self.latest = said[-1] if said else ""

    def add(self, text):
        """Save a note at the end, moving it there if we have it already, because the newest note wins."""
        if not text:
            return
        self.notes = [note for note in self.notes if note["text"] != text]
        self.notes.append({"text": text, "saved": self.today().isoformat()})
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.notes, indent=1))
        os.replace(temporary, self.path)

    def tool(self):
        """The tool that lets the model decide when to save."""

        @tool
        def remember(fact: Annotated[str, "What's worth keeping, in a few words"]) -> str:
            """Save something the user told you about themselves, for future conversations."""
            self.add(self.latest)
            return "Saved."

        return remember

    def system(self, text):
        """Add the notes to a system prompt, in the order they were saved, so the newest comes last."""
        if not self.notes:
            return text
        lines = "\n".join(f"- {note['text']}" for note in self.notes)
        return f"{text}\n\nThings this person told you before, oldest first:\n{lines}"
