"""Worked answers for chapter 30. Try the exercises first."""
import re
from typing import Annotated

from whitebox import Tool
from whitebox.tools import parameters_of


def worker_tool(agent, name, description):
    def ask(task: Annotated[str, "The whole task, with every detail"]) -> str:
        return agent.run(task).answer

    return Tool(name, description, parameters_of(ask), ask)


def pick_name(said, names):
    said = said.lower()
    return next((name for name in names if name in said), names[0])


def count_copied(reply, log):
    lines = [re.sub(r"^[\s*\-\d.)]+", "", line).strip() for line in reply.splitlines()]
    return sum(bool(line) and line.lower() != "none" and line.lower() in log.lower() for line in lines)


def add_up(logs, ask):
    return {branch: sum(count_copied(ask(text), text) for text in texts) for branch, texts in logs.items()}


def choose_architecture(job):
    if job.get("plain_code_can_do_it"):
        return "code"
    if job.get("needs_separate_permissions"):
        return "split for permissions"
    if job.get("fits_in_one_call"):
        return "add steps" if job.get("needs_more_steps") else "one agent"
    if job.get("splits_into_independent_pieces"):
        return "team"
    return "rethink the job"
