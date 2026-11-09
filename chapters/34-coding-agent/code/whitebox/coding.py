"""Tools for a coding agent: look at a project, change it, and run its tests in a sandbox."""
from pathlib import Path
from typing import Annotated

from .safety import inside
from .sandbox import Sandbox
from .tools import tool

PYTEST = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

CODING_SYSTEM = (
    "You are a coding agent. Fix the bug described in ISSUE.md. Read the code and the tests, change the code, then run the tests. "
    "When all the tests pass, reply with a short summary of what you changed."
)


def project_files(root):
    root = Path(root).resolve()
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def coding_tools(root, sandbox=None, edit="replace", feedback="full", protect=()):
    """list_files, read_file, an edit tool and run_tests, all kept inside root.

    edit is "replace" (swap one piece of text) or "whole" (write the whole file). feedback is "full" (the test output) or "short"
    (only passed or failed). protect lists folders the edit tool may not change, such as tests.
    """
    sandbox = sandbox or Sandbox(root, readonly=protect)

    def writable(path):
        full = inside(root, path)
        for folder in protect:
            if full.is_relative_to(Path(root).resolve() / folder):
                raise ValueError(f"{path} is in {folder}/, which can't be changed. Change the code, not the tests")
        return full

    @tool
    def list_files() -> str:
        """List every file in the project."""
        return "\n".join(project_files(root))

    @tool
    def read_file(path: Annotated[str, "A path from list_files, such as tests/test_stats.py"]) -> str:
        """Read one file."""
        full = inside(root, path)
        if not full.is_file():
            raise ValueError(f"there is no file called {path}")
        return full.read_text()

    @tool
    def replace_text(path: Annotated[str, "The file to change"],
                     old: Annotated[str, "Text copied exactly from the file. It must appear once"],
                     new: Annotated[str, "The text to put in its place"]) -> str:
        """Change a file by replacing one piece of text with another."""
        full = writable(path)
        if not full.is_file():
            raise ValueError(f"there is no file called {path}")
        text = full.read_text()
        found = text.count(old) if old else 0
        if found == 0:
            raise ValueError(f"that text isn't in {path}. Read the file and copy the text exactly")
        if found > 1:
            raise ValueError(f"that text is in {path} {found} times. Include more lines so it appears once")
        full.write_text(text.replace(old, new))
        return f"Changed {path}."

    @tool
    def write_file(path: Annotated[str, "The file to write"],
                   content: Annotated[str, "The whole new content of the file"]) -> str:
        """Write a whole file, replacing what was there."""
        full = writable(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        return f"Wrote {path}."

    @tool
    def run_tests() -> str:
        """Run the project's tests and show the result."""
        result = sandbox.run(PYTEST)
        if feedback == "short":
            return "All tests passed." if result.exit_code == 0 else "Some tests failed."
        return result.output

    edit_tool = {"replace": replace_text, "whole": write_file}[edit]
    return [list_files, read_file, edit_tool, run_tests]
