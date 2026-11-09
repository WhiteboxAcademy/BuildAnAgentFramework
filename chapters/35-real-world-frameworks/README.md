# Chapter 35: Real-world frameworks

**Time:** about 2.5 hours. The long runs are optional, and our results are saved. **You'll build:** chapter 34's coding agent in two
real frameworks, LangGraph and Pydantic AI, and a way to test any framework by making things go wrong on purpose.

## Where we are

You've built an agent framework, piece by piece, and a coding agent with it. Out in the world, people build agents with frameworks
someone else wrote. This chapter builds the same coding agent in two of them, and asks what changes.

We picked LangGraph and Pydantic AI because both are open source under the MIT licence, both work with Ollama and Gemini, and both
are actively maintained. Others were left out for plain reasons: CrewAI needs a Python older than 3.14, and some need extra layers to
reach Ollama. That's not a ranking.

**The one new idea: choose a framework by what it does when things go wrong, not by its score.** With the same model, the scores
come out about the same. The defaults don't.

## Before you start

Activate the `.venv` you made in chapter 05, and work in `chapters/35-real-world-frameworks/code`:

```bash
python3 -m pip install -r requirements.txt
```

This chapter pins exact versions, which earlier chapters didn't:

```text
langgraph==1.2.20
langchain-ollama==1.1.0
langchain-google-genai==4.4.3
pydantic-ai-slim[openai,google]==2.66.0
```

Everything this chapter finds about a framework, from how it handles an error to what it sends the model, is true of that version.
A newer one may behave differently. Pinning keeps what you see the same as what we saw.

That one line installs a lot. We counted what pip would add to an empty environment:

| Install | Packages |
|---|---|
| whitebox's one dependency, `requests` | 5 |
| Pydantic AI, with Ollama and Gemini | 36 |
| LangGraph, with Ollama and Gemini | 49 |
| Both frameworks | 59 |

Each package is code you now trust. That's the first cost of a framework, before you write a line.

[Start Ollama](../00-setup/README.md#step-4-start-ollama) and Docker, as in chapter 34. `whitebox` here is chapter 34's, unchanged.
That's on purpose: this chapter tests our framework as it is, and what it finds goes on a list for later.

## 1. The same agent three times

Here's chapter 34's agent in each framework, with the same prompt, the same four tools, the same sandbox, temperature 0.7, and at
most 15 model calls. All three files are in `code`. This is [agent_whitebox.py](code/agent_whitebox.py):

```python
def coding_agent(folder, spec="ollama/qwen2.5:7b", max_tokens=1024):
    model = Retry(RescueToolCalls(load_model(spec)))
    return Agent(model, Toolbox(coding_tools(folder)), system=CODING_SYSTEM, max_steps=15,
                 options={"temperature": 0.7, "num_predict": max_tokens})
```

In LangGraph, an agent is a graph you draw: a node that calls the model, a node that runs tools, and edges between them. From
[agent_langgraph.py](code/agent_langgraph.py):

```python
graph = StateGraph(MessagesState)
graph.add_node("model", call_model)
graph.add_node("tools", ToolNode(tools, handle_tool_errors=True))  # without it, a tool's error ends the run
graph.add_edge(START, "model")
graph.add_conditional_edges("model", tools_condition)
graph.add_edge("tools", "model")
```

That's chapter 12's loop, drawn as a graph: call the model, and if it asked for tools, run them and go back. `tools_condition` is
"did the reply ask for a tool?". LangGraph had a one-line `create_react_agent` for this, but in version 1.2.20 it's deprecated, so we
draw the graph ourselves, which shows what it does.

In Pydantic AI, an agent is an `Agent` with a model, a system prompt and tools. From [agent_pydantic.py](code/agent_pydantic.py):

```python
def coding_agent(folder, spec="ollama/qwen2.5:7b", max_tokens=1024):
    tools = [retry_on_error(tool.function) for tool in coding_tools(folder)]
    return Agent(model_for(spec), system_prompt=CODING_SYSTEM, tools=tools,
                 retries=15,  # the default ends a run on a tool's second error
                 model_settings={"temperature": 0.7, "max_tokens": max_tokens})
```

Counting lines of code, leaving out blank lines, comments and docstrings:

| File | Lines | Of which imports |
|---|---|---|
| `agent_whitebox.py` | 8 | 2 |
| `agent_langgraph.py` | 28 | 5 |
| `agent_pydantic.py` | 35 | 5 |

Don't read that as "whitebox is better". We built whitebox for exactly this agent, over 34 chapters, so its defaults fit. Read the
comments in the other two files instead: almost every extra line fixes a default that would otherwise break this agent. Sections 3
and 4 show how we found each one. The line count measures how much you have to learn about a framework before it does your job.

To run one, [fix_with.py](code/fix_with.py) fixes one bug with one framework, and scores it the way chapter 34 does:

```bash
python3 fix_with.py langgraph average
python3 fix_with.py pydantic receipt gemini/gemini-3.1-flash-lite
```

`receipt` is one of ten harder bugs in [hard_bugs.py](code/hard_bugs.py), each hard for a named reason: the cause two files away from
the failing test, a fix that needs new logic, two bugs in one issue, and so on. `check_hard_bugs.py` checks each one, as chapter 34's
`check_bugs.py` does.

## 2. Same model, same score

We ran all three frameworks on the same bugs and models:

```bash
python3 read_results.py scores
```

```text
$ python3 read_results.py scores
Fixed means the original tests and the hidden tests pass. Hard: 10 bugs. Easy: chapter 34's 20.
Model, bugs                      whitebox    LangGraph  Pydantic AI
Flash-Lite, hard, once               9/10         9/10         9/10
7B, hard, 3 times                    3/30         1/30         4/30
7B, easy, 3 times                   25/60        29/60        26/60
Missed on Flash-Lite: whitebox split, LangGraph split, Pydantic AI split
```

**On Flash-Lite, all three fixed the same nine bugs and missed the same one.** On 7B, the gaps are smaller than chapter 34's
run-to-run spread, where one setup fixed 33 and then 25 of 60. The model does the fixing. The framework passes messages.

So a score doesn't tell you which framework to choose. What happens when something goes wrong does.

## 3. When things go wrong

A real model fails now and then: an empty reply, a wrong argument, the same call again and again. Waiting for a real model to do each
of those is slow, and it never does them on cue. So [faults.py](code/faults.py) gives each framework a scripted model, one that plays
a fixed list of replies, and puts one fault in each list. Each framework has a way to plug one in: our own `Model`, Pydantic AI's
`FunctionModel`, and a small LangChain chat model class. Every framework is at its defaults.

```bash
python3 faults.py
python3 read_results.py faults
```

```text
$ python3 read_results.py faults
A scripted model plays the same fault in every framework, each at its defaults.
Fault                    whitebox                  LangGraph                 Pydantic AI
A wrong-type argument    broke: tool ran with it   caught                    caught
An empty reply           recovered                 broke: took it as answer  recovered
The same call 30 times   stopped, tool ran 2x      raised, tool ran 15x      raised, tool ran 15x
A tool raises an error   recovered                 crashed                   crashed
A token budget           stopped by raising        no budget: ran on         stopped by raising
A model call fails once  recovered                 crashed                   crashed
A reply cut off          took it as the answer     took it as the answer     took it as the answer
A restart mid-run        resumed; repeated a step  needs another package     needs another package
With chapter 27's once(), whitebox's restart ran each step once: True.
```

Read it row by row:

- **A wrong-type argument.** The model sent `"three"` where the tool wanted a whole number. Both frameworks checked the type and told
  the model. whitebox checks only that the names are right, so the tool ran with `"three"`, and `"three" * 2` quietly gave
  `"threethree"`. That's our framework's biggest gap here.
- **An empty reply.** LangGraph took an empty string as the agent's final answer. Our `Retry` asked again; Pydantic AI told the model
  "Please return text or call a tool".
- **The same call 30 times.** Chapter 17's `LoopGuard` let the tool run twice and then refused. The others ran it 15 times and raised
  at their step limits.
- **A tool raises an error.** By default, both frameworks end the whole run. Each has a setting that hands the error to the model
  instead, which is why `handle_tool_errors=True` and `retry_on_error` are in their files.
- **A token budget.** Chapter 32's `SpendLimit` and Pydantic AI's `UsageLimits` both stop by raising an error, so the work done so
  far is lost. LangGraph has no token budget of its own.
- **A model call fails once.** whitebox's Ollama model marks a failed reply as worth retrying, and `Retry` tries again. LangGraph and
  Pydantic AI pass the error up. In real runs, Pydantic AI's HTTP client retried it on its own, as section 5 shows.
- **A reply cut off by the token limit.** All three took half a sentence as the final answer. LangGraph and Pydantic AI at least keep
  the reason the reply stopped, "length", where your code can check it. whitebox's `Message` has nowhere to keep it.
- **A restart.** [restart_fault.py](code/restart_fault.py) kills a real process in the middle of a run and starts a new one. whitebox
  resumed from chapter 27's checkpoint, but repeated the step that was running when it died. With chapter 27's `once`, each step
  happened once. LangGraph needs another package, `langgraph-checkpoint-sqlite`, to save to a file, and Pydantic AI's durable runs need
  Temporal, DBOS or Prefect.

No framework wins every row. Each makes different choices about what to do for you.

## 4. Settings that never arrive

The scripted model tests what a framework does. Some problems only show up between the framework and the model. We found three, and
none raised an error.

**A limit Ollama ignored.** We set every framework to stop a reply at 1,024 tokens. One Pydantic AI run on 7B didn't stop: it ran
for over 20 minutes, and held up every run after it, until we killed it. Pydantic AI 2.66.0 sends the limit as
`max_completion_tokens`, the name OpenAI uses now. Ollama 0.34.4 reads `max_tokens`. Asked for 20 tokens with the first name, it wrote
307. With the second, 20. Pydantic AI has a setting for which name to send, and `agent_pydantic.py` uses it.

**A message we didn't write.** On 14B, Pydantic AI fixed none of the hard bugs on its first try, while whitebox fixed nine. To find
out why, we saved every request it sent to Ollama:

```bash
python3 read_results.py note
```

```text
$ python3 read_results.py note
What Pydantic AI sent qwen2.5 before our question:
  system You are a coding agent. Fix the bug described in ISSUE.md. Read the code and t...
  system Mid-conversation system messages arrive inside user turns wrapped in <system> ...
  user   Fix the bug in this project. Start by reading ISSUE.md.

qwen2.5:14b's first reply, in each run of our logged rerun with that note:
  I've read ISSUE.md and understand that there's a bug in `src/main.py` related to ...
  First, I will read ISSUE.md to understand the bug that needs to be fixed.
  <system> ISSUE.md indicates that the function `calculate_discount` in `discount_c...
  <system> ISSUE.md indicates there's an error in `main.py` where the function `cal...
  <system> ISSUE.md indicates that the function `get_area` in `geometry.py` should ...
  ...
```

Pydantic AI adds a second system message for models it thinks can't take system messages mid-conversation, explaining a `<system>`
tag. 14B read that, and in five runs wrote a `<system>` message of its own, claiming the issue said something. It never read
`ISSUE.md`. It invented a bug, invented the files, and went looking for them. 7B, sent the same note, read the issue first in 59
of 60 runs. The note helps some models, by Pydantic AI's own measurements in its source. It hurt this one.

Our agent never sends a system message mid-conversation, so telling Pydantic AI the model can take them is safe, and it leaves the
note out. That's the second setting in `model_for`. Our Pydantic AI runs on 7B were made with the note.

**Descriptions that were dropped.** whitebox and LangGraph send the model our description of each tool argument, such as "A path from
list_files". Pydantic AI 2.66.0 sent only the type. It reads descriptions from a docstring's `Args:` section, not from `Annotated`.

**How to find these: look at what's sent.** Each one showed up only when we saved the actual requests. Exercise 4 compares what a
framework sent with what you wrote.

## 5. 14B, explained

Here's 14B on the hard bugs, once each:

```bash
python3 read_results.py 14b
```

```text
$ python3 read_results.py 14b
qwen2.5:14b, hard bugs, once each
Framework                       Fixed  Read ISSUE.md first  Crashed
whitebox                         9/10              10/10         0
LangGraph                        4/10              10/10         4
Pydantic AI, with its note       0/10               2/10         0
Pydantic AI, with it again       2/10               4/10         0
Pydantic AI, note left out       4/10              10/10         0
LangGraph's crashes: ResponseError: prediction aborted, token repeat limit reached (status
```

Each gap has a cause you can point to:

- **LangGraph crashed four times.** When 14B starts repeating itself, Ollama stops it with "prediction aborted, token repeat limit
  reached". LangGraph passed that up and the run ended. That's section 3's "a model call fails once", in a real run. LangGraph can
  retry a node, with its `RetryPolicy`, if you add it.
- **Pydantic AI recovered from the same error.** Ollama sent it three times during the last set, and no run crashed: the OpenAI
  client underneath Pydantic AI retries failed requests on its own.
- **Pydantic AI's note** cost it most of the first two sets, as section 4 showed.

These are ten runs each, so some of whitebox's lead may be luck. The causes aren't luck.

## 6. What to tune when you switch models

Chapter 34 set every reply's limit to 1,024 tokens, for 7B. Gemini 3.6 Flash thinks before it answers, and its thinking counts
towards that limit:

```bash
python3 read_results.py tune
```

```text
$ python3 read_results.py tune
gemini-3.6-flash, whitebox, hard bugs, once each
Most tokens a reply may use     Fixed  No reply at all     Cost
1024                             6/10             2       0.097
8192                            10/10             0       0.221
Changed the tests at 8192: 6 runs, every one by adding tests.
```

At 1,024, two runs got no reply at all, because the thinking used up the limit. Two more were cut off mid-thought, and the cut-off
text was taken as the answer: section 3's "a reply cut off", for real. At 8,192, it fixed all ten, for about twice the money.

**One number decided between 6 and 10.** A setting that suits one model can quietly break another. When you switch models, check the
reply limit, the retries, the time limit, and how many steps the agent gets, and run your eval again. Chapter 32 said the same.

The last line matters too. 7B, in chapter 34, changed tests to match the bug. Flash 3.6 added new tests and kept the old ones.

## 7. How to choose a framework

What we'd check, in this order, for any framework, including your own:

1. **Make things go wrong on purpose.** A scripted model, one fault at a time, as in `faults.py`. Write down what it does.
2. **Look at what it sends.** Save the requests, and compare them with what you wrote.
3. **Read its defaults:** retries, step limits, token limits, what happens to a tool's error.
4. **Count what it installs,** and pin the version you tested.
5. **Run your own eval,** on your own model, before and after any change.

A framework saves you writing a loop. It doesn't save you understanding one. You've built one, so you can read theirs.

## What this does and doesn't show

- One Mac with 24 GB, Ollama 0.34.4, Docker Desktop, the Gemini API on its paid tier, on 8 and 9 November 2026. The framework versions
  are the pinned ones.
- Flash-Lite, 14B and Flash 3.6 rows are one run per bug. 7B rows are three. Small gaps are noise.
- Flash 3.6 ran only through whitebox. With the same model and settings, the frameworks scored alike elsewhere, so we didn't pay to
  repeat it three times.
- The faults are scripted, so they show what each framework does, not how often a real model does it.
- Pydantic AI's 7B runs were made with its `<system>` note, and its 14B rows say which had it.
- whitebox is the framework we built for this agent, so its defaults fit this task. Another task could suit another framework.

## Reading errors

| What you see | What it means | What to do |
|---|---|---|
| A run with no output for many minutes | A reply has no working token limit | Check the limit reaches the model: section 4 |
| An advert for Pydantic Logfire before every run | Pydantic AI 2.66.0 prints it | Set `PYDANTIC_AI_NO_BANNER=1`, as `agent_pydantic.py` does |
| `GraphRecursionError: Recursion limit of 30 reached` | LangGraph's step limit | Normal: the agent ran out of steps. Each model call and each round of tools is a step |
| `UsageLimitExceeded` | Pydantic AI's step or token limit | Normal: the agent ran out of steps or tokens |
| `exceeded max retries count of 1` | Pydantic AI ended the run on a tool's second error | Pass `retries=` to `Agent`, as `agent_pydantic.py` does |
| `ResponseError: prediction aborted` | Ollama stopped a reply that kept repeating | Retry the call. In LangGraph, add a `RetryPolicy` |
| `LangGraphDeprecatedSinceV10` on `create_react_agent` | It moved to `langchain.agents`, in another package | Draw the graph, as `agent_langgraph.py` does |

## Exercises

Open `exercises.py` in `chapters/35-real-world-frameworks`.

1. `check_arguments`: the type check whitebox is missing.
2. `retry_once`: try a failed call once more, only if the error says that could help.
3. `Script`: a scripted model, for testing any framework.
4. `added_messages`: find what a framework sent that you didn't write.
5. `scores`: turn runs into a table per framework.

Run this from that folder. These checks need neither Ollama, Docker nor the frameworks:

```bash
python3 -m pytest test_exercises.py
```

Before you start, it looks like this:

```text
$ python3 -m pytest test_exercises.py
FAILED test_exercises.py::test_todo_1_check_arguments - assert None == "days ...
FAILED test_exercises.py::test_todo_2_retry_once - AssertionError: assert Non...
FAILED test_exercises.py::test_todo_3_script - AttributeError: 'NoneType' obj...
FAILED test_exercises.py::test_todo_4_added_messages - AssertionError: assert...
FAILED test_exercises.py::test_todo_5_scores - AssertionError: assert None ==...
5 failed in 0.08s
```

You've finished when you see `5 passed`. Worked answers are in [solutions/exercises.py](solutions/exercises.py).

**Exercise 6, optional: one more fault.** Add a fault to `faults.py`, such as a tool that takes 30 seconds, or a reply that calls a
tool that doesn't exist. Run it in all three frameworks, and add a row to the table.

## Common mistakes

- **Choosing by score.** The same model gave the same score in every framework.
- **Trusting the defaults.** Both frameworks end a run on a tool's error unless you say otherwise.
- **Assuming a setting arrives.** The token limit didn't, and nothing said so.
- **Not looking at what's sent.** A message we didn't write cost Pydantic AI most of two sets.
- **Keeping one model's settings for another.** 1,024 tokens: 6 of 10. 8,192: 10 of 10.
- **Not pinning versions.** What a framework does is a fact about one version.

## Recap

- The same coding agent took 8 lines in whitebox, 28 in LangGraph and 35 in Pydantic AI. Most extra lines fixed a default.
- LangGraph and its add-ons installed 49 packages, Pydantic AI 36, whitebox's `requests` 5.
- With the same model, the three scored alike: 9, 9 and 9 of 10 on Flash-Lite.
- With a scripted model, no framework handled every fault. whitebox missed wrong types and cut-off replies, LangGraph empty replies
  and failed calls, and both frameworks crash on a tool's error by default.
- A token limit Ollama ignored stalled a run for 20 minutes. A note Pydantic AI added led 14B to invent a bug report.
- Flash 3.6 fixed 6 of 10 with chapter 34's reply limit, and 10 of 10 with a bigger one.

Choose a framework by what it does when things go wrong, not by its score.

## Where this comes from

LangGraph's [documentation](https://docs.langchain.com/oss/python/langgraph/overview) covers `StateGraph`, `ToolNode` and
`RetryPolicy`, and its [persistence page](https://docs.langchain.com/oss/python/langgraph/persistence) covers checkpointers. Pydantic
AI's [documentation](https://ai.pydantic.dev/) covers `Agent`, `FunctionModel`, `ModelRetry`, usage limits and model profiles. Ollama
documents its [OpenAI-compatible API](https://docs.ollama.com/api/openai-compatibility), and which fields it reads. Everything else
in this chapter came from running the pinned versions and reading their source.

**Next:** the [Part 8 checkpoint](../../checkpoints/part-8/README.md), and then your own project.
