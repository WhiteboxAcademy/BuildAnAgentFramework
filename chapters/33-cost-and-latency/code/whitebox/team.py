"""Teams: an agent can be a tool for another agent, and a router can choose who answers."""
from dataclasses import dataclass, field
from typing import Annotated

from .messages import Message
from .tools import Tool, parameters_of


def agent_tool(agent, name, description):
    """Turn an agent into a tool. Each task starts a fresh chat, so the task must say everything."""

    def ask(task: Annotated[str, "The whole task, with every detail from the user"]) -> str:
        return agent.run(task).answer

    return Tool(name, description, parameters_of(ask), ask)


@dataclass
class Router:
    """One model call picks a worker, then that worker does the whole job."""

    model: object
    workers: dict
    chosen: list = field(default_factory=list)

    def pick(self, question):
        names = "\n".join(f"{name}: {description}" for name, (description, _) in self.workers.items())
        prompt = f"Who should handle this request?\n{names}\n\nRequest: {question}\n\nReply with only the name."
        said = self.model.chat([Message("user", prompt)], temperature=0).content.lower()
        return next((name for name in self.workers if name in said), next(iter(self.workers)))

    def run(self, question):
        name = self.pick(question)
        self.chosen.append(name)
        return self.workers[name][1].run(question)
