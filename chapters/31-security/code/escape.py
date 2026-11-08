"""Four paths a model might send to read_file. No model needed."""
import os
import tempfile
from pathlib import Path

from office import make_office, open_tools, WORDINGS
from whitebox import ToolCall, Toolbox, folder_tools

with tempfile.TemporaryDirectory() as name:
    work = make_office(Path(name), WORDINGS["clean"])
    os.symlink(work.parent / "private/staff_pay.txt", work / "inbox/notes.txt")
    paths = ["inbox/01-harbour.txt", "../private/staff_pay.txt", str(work.parent / "private/staff_pay.txt"), "inbox/notes.txt"]
    labels = ["a file in the inbox", "climbs out with ..", "a full path", "a link in the inbox"]
    print("The full path is", paths[2].replace(name, "/tmp/office"))
    for title, tools in [("Chapter 14's read_file", open_tools(work)), ("folder_tools", folder_tools(work))]:
        print(title)
        toolbox = Toolbox(tools)
        for label, path in zip(labels, paths):
            output = toolbox.run(ToolCall("read_file", {"path": path}))
            for real in (os.path.realpath(name), name):
                output = output.replace(real, "/tmp/office")
            print(f"  {label:<22}{' '.join(output.split())[:72]}")
