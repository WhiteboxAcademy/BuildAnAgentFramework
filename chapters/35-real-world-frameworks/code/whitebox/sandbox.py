"""Run code in a Docker box: no network, limited memory, a time limit, and only one folder visible."""

import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

IMAGE = "whitebox-sandbox"


@dataclass
class RunResult:
    exit_code: int
    output: str
    seconds: float
    timed_out: bool = False


class Sandbox:
    def __init__(self, project, readonly=(), image=IMAGE, seconds=20, memory="256m", max_output=4000):
        self.project = Path(project).resolve()
        self.readonly = list(readonly)
        self.image = image
        self.seconds = seconds
        self.memory = memory
        self.max_output = max_output

    def command(self, argv, name):
        mounts = ["-v", f"{self.project}:/work"]
        for folder in self.readonly:
            mounts += ["-v", f"{self.project / folder}:/work/{folder}:ro"]
        return [
            "docker", "run", "--rm", "--name", name,
            "--network", "none",
            "--memory", self.memory, "--cpus", "1", "--pids-limit", "64",
            "--read-only", "--tmpfs", "/tmp",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            *mounts, "-w", "/work", self.image,
            "timeout", str(self.seconds), *argv,
        ]

    def run(self, argv):
        name = f"whitebox-{uuid.uuid4().hex[:12]}"
        start = time.monotonic()
        try:
            done = subprocess.run(self.command(argv, name), capture_output=True, text=True,
                                  timeout=self.seconds + 30)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            return RunResult(124, "timed out", time.monotonic() - start, timed_out=True)
        output = done.stdout + done.stderr
        if len(output) > self.max_output:
            output = "...\n" + output[-self.max_output:]
        timed_out = done.returncode == 124
        if timed_out:
            output += f"\nStopped after {self.seconds} seconds."
        elif done.returncode == 137:
            output += f"\nStopped: it used more than {self.memory} of memory."
        return RunResult(done.returncode, output, time.monotonic() - start, timed_out)
