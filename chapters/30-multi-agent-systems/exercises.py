"""Chapter 30 exercises. Complete each TODO, then run: python3 -m pytest test_exercises.py"""
import re  # Provided: you'll need this.
from typing import Annotated

from whitebox import Tool
from whitebox.tools import parameters_of


def worker_tool(agent, name, description):
    """TODO 1: The heart of agent_tool. Return a Tool that an Agent can call, with this name and description. It
    takes one argument, task, a string. Running it calls agent.run(task) and returns the result's answer. Write an
    inner function with task as Annotated[str, "..."], and use parameters_of(your_function) for the parameters.
    """
    return None


def pick_name(said, names):
    """TODO 2: The heart of Router.pick. said is the model's reply, and names is a list of workers, in lower case.
    Return the first name in the list that appears anywhere in said, ignoring case. If none does, return names[0],
    so an unclear reply still goes somewhere.
    """
    return None


def count_copied(reply, log):
    """TODO 3: A worker copies sentences out of a log, one per line. Return how many lines of reply really appear in
    log. Remove any leading spaces, dashes, stars, digits, dots and brackets from each line first, and strip it.
    Ignore empty lines and the word none. Compare without caring about case, because a model may lower-case a line.
    """
    return None


def add_up(logs, ask):
    """TODO 4: Split the job, and keep the count in code. logs is a dictionary of branch name to a list of log texts.
    ask(text) returns a worker's reply for one log. Return a dictionary of branch name to the total of count_copied
    for that branch's logs.
    """
    return None


def choose_architecture(job):
    """TODO 5: The chapter's chooser. job is a dictionary of True or False values. Check them in this order, and return
    the first answer that applies:
    plain_code_can_do_it -> "code"
    needs_separate_permissions -> "split for permissions"
    fits_in_one_call and needs_more_steps -> "add steps"
    fits_in_one_call -> "one agent"
    splits_into_independent_pieces -> "team"
    Anything else -> "rethink the job"
    """
    return None
