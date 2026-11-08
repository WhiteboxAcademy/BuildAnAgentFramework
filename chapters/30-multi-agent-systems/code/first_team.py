"""A manager with two workers. Each worker is a whole agent, used as a tool."""
from team_setups import Setups
from whitebox import load_model

QUESTION = "How much stock was lost when the Harbour cellar flooded?"

manager = Setups(load_model()).manager()
result = manager.run(QUESTION)
print("Staff asked:", QUESTION)
for message in result.messages:
    for call in message.tool_calls:
        print(f"Manager called {call.name}, with task: {call.arguments.get('task')}")
    if message.role == "tool":
        print("Worker answered:", " ".join(message.content.split()))
print("Manager said:", " ".join(result.answer.split()))
