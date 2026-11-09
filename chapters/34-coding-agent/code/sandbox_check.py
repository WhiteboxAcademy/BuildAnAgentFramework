"""Try to break out of the sandbox, and see what stops each try.

    python3 sandbox_check.py

Makes a tiny project in your temporary folder, with its tests read-only, and runs each try inside the whitebox-sandbox image. Every
try is something an agent's code could do by mistake, or on purpose.
"""
import shutil
import tempfile
import time
from pathlib import Path

from whitebox.sandbox import Sandbox

TRIES = {
    "run the tests": ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
    "reach the internet": ["python", "-c", "import urllib.request; urllib.request.urlopen('http://example.com', timeout=5)"],
    "change the tests": ["sh", "-c", "echo x >> tests/test_calc.py"],
    "change the code": ["sh", "-c", "echo '# changed' >> calc.py && echo changed"],
    "write outside": ["sh", "-c", "echo x > /etc/x"],
    "fill 600 MB": ["python", "-c", "x = b'x' * (600 * 1024 * 1024); print('got it')"],
    "loop for ever": ["python", "-c", "while True: pass"],
    "start 200 processes": ["python", "-c", "import os, time\nfor i in range(200):\n    try:\n        os.fork() or time.sleep(5)\n"
                            "    except OSError:\n        print('stopped after', i); break"],
    "look at your files": ["sh", "-c", "ls /Users 2>&1"],
}

tmp = tempfile.mkdtemp()
try:
    project = Path(tmp) / "project"
    (project / "tests").mkdir(parents=True)
    (project / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (project / "tests" / "test_calc.py").write_text("from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n")
    box = Sandbox(project, readonly=["tests"], seconds=5)
    print(f"{'Try':<22}{'Exit':>5}{'Seconds':>9}  Last line")
    for label, argv in TRIES.items():
        result = box.run(argv)
        lines = result.output.strip().splitlines()
        print(f"{label:<22}{result.exit_code:>5}{result.seconds:>9.1f}  {lines[-1][:58] if lines else ''}")
finally:
    # Docker can hold the read-only tests/ for a moment after the last run, so deleting it may fail at first.
    for _ in range(10):
        shutil.rmtree(tmp, ignore_errors=True)
        if not Path(tmp).exists():
            break
        time.sleep(0.5)
