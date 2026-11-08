# Chapter 30: Multi-agent systems

**Time:** about 3 hours. The long runs are optional, and their results are saved. **You'll build:** a team of agents, and the
judgement to know when not to use one.

## Where we are

Part 6 ended with an agent that can use tools it doesn't own. It's still one agent, doing one job at a time. This chapter starts
Part 7, where the agent has to meet the real world: other agents, attackers, other models and a bill.

You'll hear that the next step is obvious: split the work between several agents, the way a company splits work between people.
Sometimes that's right. Often it isn't. So this chapter does something a little different. It teaches one new idea, then it
tests that idea on six kinds of job, and shows you where it won, where it lost and where it only looked as if it won.

The new idea is small: **an agent can be a tool for another agent.** The goal is bigger: by the end, you should be able to look at
a job and choose an architecture, with a reason.

## Before you start

Activate the `.venv` you made in chapter 05, and work in `chapters/30-multi-agent-systems/code`:

```bash
python3 -m pip install -r requirements.txt
```

[Start Ollama](../00-setup/README.md#step-4-start-ollama). `read_results.py` doesn't need it. Every other script does.

`whitebox/team.py` is new in this chapter, and it's already written. You'll read all of it. These files sit beside it:

- `team_setups.py` is provided. It builds the setups we compare, so each script can stay short.
- `results/chapter30.json` holds our saved runs, and `read_results.py` prints them.
- `compare_teams.py` and `two_steps.py` are the long runs. They're optional, and they take about 50 and 7 minutes.
- Each other script is explained in the section that uses it.

To check the framework itself, run this from `code`:

```bash
python3 -m pytest tests
```

## 1. The number to beat

Before you build a team, you need something to compare it with. Chapter 29's eval has 42 questions, run three times each. One
agent with one search tool, searching the handbook and the records together, scored **113 of 126**, using 260 model calls.

That's the number to beat. Everything in this chapter gets measured against the simplest thing that could work.

## 2. An agent as a tool

Here's all of [whitebox/team.py](code/whitebox/team.py), starting with the one idea:

```python
def agent_tool(agent, name, description):
    """Turn an agent into a tool. Each task starts a fresh chat, so the task must say everything."""

    def ask(task: Annotated[str, "The whole task, with every detail from the user"]) -> str:
        return agent.run(task).answer

    return Tool(name, description, parameters_of(ask), ask)
```

A `Tool` is a name, a description, some parameters and a function. Nothing says that function can't run a whole agent. So `ask`
runs one, and returns its answer as plain text. To the agent calling it, this looks like any other tool. `Agent` didn't change.

Two things follow from this:

- **The worker starts with an empty chat.** It sees the task and nothing else. If the manager leaves a detail out, the worker
  never knows it existed. That's why the parameter's description asks for every detail.
- **The manager sees only the answer.** The worker's searches stay inside the worker. That's a real benefit, because the
  manager's window doesn't fill up with them.

[code/first_team.py](code/first_team.py) gives a manager two workers: one knows the handbook, and one knows the records. Each has
its own search over its own documents. **Predict:** how many model calls does one question take now?

```text
$ python3 first_team.py
Staff asked: How much stock was lost when the Harbour cellar flooded?
Manager called ask_records, with task: How much stock was lost when the Harbour cellar flooded?
Worker answered: The stock loss when the Harbour cellar flooded, according to the log, was worth £640, mostly in paper cups and syrups. [log-harbour-2025-02.md]
Manager said: When the Harbour cellar flooded, the stock loss was worth £640, mostly in paper cups and syrups. [log-harbour-2025-02.md]
```

It worked, and the manager passed the question on word for word. It took four model calls: two for the manager, and two for the
worker. One agent answers the same question in two.

## 3. A router

A manager decides who to ask inside its own loop, and reads the answer afterwards. A **router** is cheaper. One model call picks a
worker, and that worker does the whole job:

```python
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
```

`workers` maps a name to a pair: a description of the job, and the agent. `next` from chapter 04 can take a second value, which it
returns if nothing matches. So this gives the first name found in the reply, or the first worker if the reply is unclear. `temperature=0` makes the choice as steady as it can be, because
this is a decision, not writing.

**Predict:** [code/first_router.py](code/first_router.py) asks four questions. Two belong to the handbook and two to the records.
How many will reach the right worker?

```text
$ python3 first_router.py
handbook  How much is the till float?
          The initial float for each till is £150. [cash-handling.md]
handbook  How much did the film crew pay to use Old Mill?
          I don't know. The handbook does not contain information about payments to the film crew for usin
handbook  Who was the guest at the Riverside cupping club in June 2025?
          I don't know the specific guest for the Riverside cupping club in June 2025 based on the informa
records   How much extra do oat, soya and coconut milk cost?
          I don't know the specific extra costs for oat, soya, and coconut milk from the information provi
```

Only one of the four went to the right worker. The film crew and the cupping guest are in the records, and they went to the
handbook. The milk charge is in the handbook, and it went to the records. Each worker then honestly said it didn't know, because it
couldn't see the answer. Nothing crashed. The team just failed quietly.

## 4. Does the team beat one agent?

**Predict before you read on.** Specialists have smaller, cleaner indexes. Will they beat 113? Will the extra calls be worth it?

We ran the same eval on each setup. `two tools` is one agent that has to choose between a handbook search and a records search.
`compare_teams.py` does this, in about 50 minutes. Here are our results:

```text
$ python3 read_results.py teams
Setup                  Of 126  Calls  Tokens in  Seconds
one agent                 113    260    111,692      400
two tools                  88    287    163,105      555
router                     96    384    116,254      425
router, new wording        94    392    135,943      422
manager                    92    499    191,316      692
strict manager            102    595    248,246      865
perfect router            113    252    100,658      396
```

Every real team did worse than one agent, and every one cost more.

Reading the failed answers shows why. **Splitting the documents created a decision, and that decision can go wrong.** One agent
searching everything never has to choose. The router sent 108 of 126 questions to the handbook, when 96 belonged there. So on
`records` questions, it got 12 of 24, against 24 of 24 for one agent.

The second-last row is a fair test of the manager. On its first prompt, it answered 10 runs without asking anyone, saying "I don't
know" to questions like "What does E44 mean?". So we told it to always ask a colleague, and to try the other one before giving up.
That raised it from 92 to 102, and raised its calls from 499 to 595. Better, and still behind.

Rewording the router's job descriptions did something else worth seeing. It fixed the `direct` questions, then made other questions
worse. Wrong routes went from 18 to 33, and the score didn't improve. **Wording moved the mistakes around.**

The last row is the one that matters. `perfect router` is a cheat: we told it the right worker every time. So it shows the best any
router could ever do with these two workers. **It tied at 113.** With routing solved completely, the specialists gained nothing.
A better router, or a better model, can only catch up with one agent here.

Here's something we got wrong. We expected details to get lost as tasks passed between agents, like a message passed along a line.
They didn't. The manager passed 114 of 126 tasks on word for word, or 116 with the strict prompt, and it lost a worker's right answer at most once per setup. On
this model and these questions, the handoff wasn't the weak point. The choice was.

## 5. What a team costs

Look at the calls again: 260 for one agent, 595 for the strict manager, and 865 seconds against 400. A team multiplies cost in a
second way too, one that doesn't show up in a table.

An `Agent` stops after `max_steps`, which is 8 by default. A manager has 8 steps, and each step can start a worker with 8 steps of
its own. So one question can now cost more than 60 model calls, not 8. We saw 10 at most, but the limit you thought you had has gone.
If you build a team, think about the limit for the whole team, not for one agent.

## 6. A worker that never returns

While these runs were going, one of them stopped moving. Python used almost no processor time, and Ollama was running flat out. Our
log showed nothing for 13 minutes. We never saw that reply, but we believe a later one was the same fault, caught by a limit:

```text
$ python3 read_results.py runaway
Question: How much did the Riverside roof repair cost in 2025?
Tokens written: 1,054
Start: I couldn't find any specific information about a roof repair cost for Riverside in 2025. The logs do not mention any roof repairs or their associated 
End:   ide-2025-08.md] [log-riverside-2025-05.md] [log-riverside-2025-02.md] [log-riverside-2025-08.md] [log-riverside-2025-05.md] [log-riverside-2025-02.md]
```

The model started a sensible answer, then listed the same file names over and over. Chapter 27 met this with tool calls. It's rare.
In one agent, it's an annoying stall. In a team, one stuck
worker blocks the manager and everyone waiting on it.

The timeout didn't save us, and that's the interesting part. `OllamaModel` waits 180 seconds, but that's a limit on silence. A
runaway stream is never silent, so it never times out. What it needs is a limit on length. So `OllamaModel` now sends one:

```python
LONGEST_REPLY = 1024  # tokens. A stream that never ends never times out, so a reply needs a limit.
```

```python
"options": {"num_predict": LONGEST_REPLY, **options},
```

`num_predict` tells Ollama to stop after that many tokens. Your own options come second, so you can raise it for one call. The one
above stopped after 30 seconds, not 13 minutes. Two things about this limit: a capped reply just ends, so it may stop mid-sentence,
and it's the same fix for one agent or for a hundred.

This fix starts in this chapter. Earlier chapters keep their code, and [docs/troubleshooting.md](../../docs/troubleshooting.md)
explains what to do if a run there seems frozen.

## 7. So where should a team win?

So far, one agent has won. That's one kind of job, though, and it would be wrong to stop here. What does published work say?

Studies point to the same few conditions:

- **The work is too big for one context, and it splits cleanly.** Google's Chain of Agents beat retrieval on all eight datasets it
  was tested on, with bigger gains on longer inputs. Anthropic's research system did best on jobs like finding the board members of
  every company in a large index.
- **The pieces are independent.** A study from Google, DeepMind and MIT found teams gained 80.8% on finance work that splits into
  separate parts, and lost up to 70% on planning, where each step depends on the last.
- **A few other reasons aren't about accuracy.** Parts may need different permissions, or another company may own part of the system.

There's also a warning. **Many reported wins may just be extra compute.** Anthropic reports that token use alone explained 80% of the
variance on one test, and its teams used about 15 times the tokens of a chat. When Tran and Kiela held the budget equal, single agents
matched or beat teams on multi-hop questions. A study on a 7B model, the size we use, reached the same conclusion.

So every test from here on asks two questions: did the team win, and was it the team that won? Each test has a fair rival.

## 8. More agents, or more steps?

Hop questions need two facts from two documents. So a relay sounds right: one agent finds the first fact, and passes it to a second.
Its rival is one agent told to do **the same two steps**, in one chat, so the team doesn't win just by doing more work.
[code/two_steps.py](code/two_steps.py) runs all three, and takes about 7 minutes:

```python
def relay(question):
    note = setups.one_agent().run(question + FIRST).answer
    return setups.one_agent().run(f"{question}\nA colleague found: {note}\nFind what's still missing, then answer.").answer


def one_agent_two_steps(question):
    agent = setups.one_agent()
    first = agent.run(question + FIRST)
    return agent.run(f"{question}\nFind what's still missing, then answer.", first.messages).answer
```

**Predict:** which comes out on top? We expected one agent to win, because the steps depend on each other.

```text
$ python3 read_results.py relay
Setup                 Five passes, of 30  Of 150  Calls per pass
one agent             11 11 11 10 10          53              61
relay of two agents   17 20 18 18 20          93             117
one agent, two steps  17 15 16 14 13          75              98
```

We got this wrong twice. First, the relay beat one agent easily. Then, after one pass, the relay and two steps tied at 17, and we wrote
that the second agent added nothing. The next pass came out 20 to 15, so we ran it five times. **One pass wasn't enough to say.**

Here's what five passes show:

- **A second step helped.** One agent often stops after its first search. Two steps took it from 53 to 75. Chapter 26 saw the same
  thing with `Plan` and `Split`.
- **The relay did better again,** at 93. It won four passes and tied one, using about a fifth more calls.

Now look at the code. The relay's two "agents" are the same model, with the same prompt and the same tool. The second one isn't a
specialist. The real differences are that it starts a **clean chat**, holding only the note, and that its prompt calls the note a
colleague's. So this may say more about clean context than about teamwork. We didn't test which part did it. A long chat full of old
search results may simply be harder to read, which fits what chapter 24 found.

So a relay can earn its place on dependent steps, and it's worth trying after you've tried more steps. Published work reports the
opposite on sequential planning, which is a good reason to test your own job. Six questions is a small set.

## 9. A second opinion

People check each other's work, so an agent could too. A fresh reviewer has no stake in the first answer, and it starts with a clean
chat. Here it's a separate agent with its own search, told not to trust the draft. Its rivals are the same agent checking itself,
and a plain vote: ask three times and keep the answer most like the others.

**Predict:** will a fresh reviewer fix more than it breaks?

```text
$ python3 read_results.py review
Setup            Of 126 Fixed Broke Extra calls
first               110     -     -         270
self-check          109     3     4         126
fresh reviewer      110     5     5         252
vote of 3           112     7     5         540
```

`Extra calls` is what each row added. `Vote of 3` includes two more full runs.

The reviewer fixed 5 answers, and it broke 5. Self-checking fixed 3 and broke 4. The vote's two extra points are within the noise, and
it took three times the calls. This fits published work: a model checking itself mostly moves errors around, and debate between copies
of one model generally doesn't beat a simple vote. A reviewer may do better when it's a different, stronger model, or when
it checks something a program can confirm. We haven't tested those here. Chapter 32 gives you a second model to try.

## 10. Too much at once

Here's a different shape of job: a pile of independent questions. You could put them all in one chat, or give each its own.
[code/too_much_at_once.py](code/too_much_at_once.py) tries both. **Predict:** which breaks first?

```text
$ python3 too_much_at_once.py
10 in one chat:  9 of 10 right, 2 model calls
  It said: 1. The house blend recipe uses 18 grams of coffee to give 36 grams of espresso. [espresso-
10 chats of one: 8 of 10 right, 20 model calls
20 in one chat:  0 of 20 right, 2 model calls
  It said: I found that the Old Mill branch shares its building with the roastery, and visitors may w
20 chats of one: 17 of 20 right, 40 model calls
```

Twenty questions in one chat didn't get worse. It got none right. The model made 20 searches in one reply, the results overflowed the
window, and the answer stopped making sense. There was no error. That's chapter 24's silent cut again. Here's the full run, 108 questions
for each row:

```text
$ python3 read_results.py batch
In one chat   Window Right   Of Calls
1            default    93  108   221
5            default    57  108    68
10           default    84  108    27
20           default     0  108    13
36           default     0  108     6
36             16384    83  108     7
```

So one chat each wins, and this is what the studies call a parallel job. Look at the last row, though. The same 36 questions in a
**bigger window** got 83, in 7 calls, against 93 in 221. Whether that gap is worth 30 times the calls depends on the job.

One row doesn't fit the pattern: five at a time did worse than ten. We ran it again, in case it was a fault in our test, and got 56.
Reading the replies showed why. The model often answered only part of the list. We don't know why five is worse than ten. That's a
reminder that this model's behaviour isn't a smooth curve.

Chapter 29's forty long tools gave the same result. A router into four groups did rescue them, but a bigger window did better:

```text
$ python3 read_results.py tools
Setup                             Right Wrong None Calls Read at most
one agent, 40 tools                  12    21   27    60        2,050
one agent, 40 tools, big window      56     0    4    60        6,352
router, 4 groups                     44     6   10   120        1,835
```

## 11. Too big for any window

Now a job that can't be solved with a bigger window. Quillon has 48 monthly branch logs, about 60,000 tokens, and this model's limit
is 32,768. The question: how many deliveries were late in 2025, at each branch? The answer is spread across the whole year.

The logs were built from templates, so we can count the true answer exactly. That lets us mark every setup properly.

Here are the two fair rivals, and the team:

- **One agent with search** sees three chunks at a time.
- **One call with everything** asks for a window of 98,304.
- **A team** gives each log to its own worker, which is one model call on a small piece. Then code adds up the results.

The workers can report in two ways. They can **count** and give a number, or they can **copy** each matching sentence, and code counts
the lines. Remember Part 5's theme: let the model make the judgement call, and keep the facts in code. Here's how that looks, from
[code/big_job.py](code/big_job.py):

```python
ASK = "Copy every sentence that says a delivery was late, one per line. If there are none, reply: none"


def copied(reply, log):
    """Count only the lines that really appear in the log, so a stray line can't add to the total."""
    lines = [re.sub(r"^[\s*\-\d.)]+", "", line).strip() for line in reply.splitlines()]
    return sum(bool(line) and line.lower() != "none" and line.lower() in log.lower() for line in lines)
```

`copied` checks that each line really is in the log, so "Here are the sentences:" can't add one to the total. The `.lower()` calls
matter. Our first version compared the text exactly, and the team seemed to collapse: it found 7 run-outs out of 166. The workers had
copied every sentence correctly, and lower-cased the first letter. **When a result looks too bad, suspect your test.**

**Predict:** will the 48 small workers beat one big call? This takes a few minutes:

```text
$ python3 big_job.py
48 logs, 245,680 characters

Branch      Exact pattern Word delivery  Team of 12
harbour                45            86          43
old-mill               38            75          46
riverside              51           105          48
station                41            78          38
```

`Exact pattern` is the true count. `Team of 12` is 12 workers per branch, so 48 in all. Those team numbers add up to 175, the true
total, in this run, and that's partly luck: every branch was wrong, by 2 to 8. Here's every try, for three different counts. "Off
by" is the average gap between the answer and the truth, across the four branches. The `baked` count leaves out milk, so it needs
some judgement:

```text
$ python3 read_results.py logs
How far off each try was, on average across the four branches
Count    Setup                       Off by
late     one agent, search           98%, 98%, 98%
late     one call, everything        74%, 72%, 72%
late     team of 48, workers count   37%, 40%, 38%
late     team of 48, code counts     3%, 16%, 12%
late     team of 4, code counts      78%
late     text search, obvious word   96%
ran-out  one agent, search           2493%, 2276%, 1175%
ran-out  one call, everything        71%, 72%, 71%
ran-out  team of 48, workers count   22%, 21%, 24%
ran-out  team of 48, code counts     28%, 27%, 27%
ran-out  team of 4, code counts      158%
ran-out  text search, obvious word   0%
baked    one agent, search           100%, 5194%, 100%
baked    one call, everything        60%, 60%, 60%
baked    team of 48, workers count   39%, 45%, 46%
baked    team of 48, code counts     43%, 42%, 38%
baked    team of 4, code counts      64%
baked    text search, obvious word   38%
```

This is the team's real win:

- **One call couldn't do it.** We asked for 98,304 tokens, and it read 16,386, about a quarter of the logs. There was no error. Then it
  mostly copied our format example, saying 12 for every branch.
- **Search couldn't do it.** You can't count what you can't see, so it was off by 98% on late deliveries, and it made up huge numbers
  for run-outs.
- **48 small workers got closest.** They were off by 3% to 16% on late deliveries, and 21% to 46% on the others.
- **Small pieces mattered.** The team of 4 gave each worker a whole year, and it was erratic. It replied "none" for one branch, and for
  another it listed far more lines than exist. So splitting wasn't enough. The pieces had to be small.
- **Copying into code helped on one count.** It took late deliveries from about 38% to about 10%. On run-outs it was slightly worse,
  and on baked goods it made no real difference. It's a good habit, and it isn't magic.

Now be honest about how good this is. Copying into code named the worst branch in 1 of 9 tries. Being 27% off isn't a number
you'd put in a report.

And look at the bottom of each block. **Plain text search got run-outs exactly right**, with no model at all. A good pattern does the
same for late deliveries. The obvious word, `delivery`, was wrong, because it also finds "Delivery arrived on time". For a job
that's really just counting a pattern, plain code beats every agent setup in this chapter.

## 12. Choosing an architecture

Here's what six tests showed:

| The job | What won | Why |
|---|---|---|
| Small questions, one agent can see everything | **One agent** | A split adds a decision that can go wrong, and a perfect router only tied |
| Steps that depend on each other | **A relay** (93 of 150), then one agent with two steps (75), then one agent (53) | A second step gave about half the gain, and a clean chat may give the rest |
| Checking an answer | **Nobody**, on one model | The reviewer fixed as many as it broke |
| Too many tools for the window | **A bigger window** (56), then a router (44), against 12 | The tools fit once the window grew |
| Many independent questions | **One chat each** on score (93), a bigger window on cost (83, 7 calls) | Past the window, one chat scored 0 |
| Too big for any window, and it splits cleanly | **A team of small workers** | Nothing else could do it, and it's still only approximate |

So here's a way to choose. Ask these in order, and stop at the first yes:

1. **Can plain code do it?** Use code. It's exact, free and fast.
2. **Do parts need different permissions, or does someone else own them?** Split for that reason. Chapter 31 tests this.
3. **Does it fit in one call, or in a bigger window?** Use one agent. If it needs more thinking, add steps first.
4. **Does it split into small, independent pieces?** Use a team of small workers, and let code join the results.
5. **None of those?** Rethink the job before you add agents.

Then measure your choice against the simpler option at the same budget, and keep the team only if it wins.

Try it on these, then check your reasoning in exercise 5:

- *"Read every review from last year, and pull out each complaint about delivery."* Too big, splits by review: a team of small workers.
- *"Answer staff questions about the handbook."* Fits: one agent.
- *"Add up the till takings from a spreadsheet."* Plain code.
- *"Plan a store's move, where each step changes the next."* Fits, needs thought: one agent with more steps, then try a relay.
- *"Read customer emails, and also send refunds."* Separate permissions. That's the next chapter.

## What this does and doesn't show

- We ran one Mac, `qwen2.5:7b` at temperature 0.7, and one fictional company. A stronger model could change any row here, the router
  and the reviewer most of all.
- Three runs of 42 questions can show a big gap, but not a small one. Run to run, scores move by a few points. The team
  setups are too close to rank against each other, and the gap to 113 is too big to be noise.
- We tried two wordings of the router and two prompts for the manager. A better prompt could do better. The perfect router shows the
  limit on these questions, and that limit is a tie.
- The logs came from templates, which suits plain text search. Real logs are messier, and a pattern would do worse. We didn't test that.
- The workers ran one after another. Running them at the same time could make a team faster, and we haven't measured that here.
- The "team" in the logs test is close to a simple loop. There's no conversation between agents. That's the point, and it means this
  test says nothing about agents that talk to each other.
- The 80.8%, 15 times and other published figures come from other people's models and tasks.

## Reading errors

| What you see | What it means | What to do |
|---|---|---|
| A worker says "I don't know" about something you know is there | It went to the wrong worker, or the wrong search | Print `router.chosen`, or the manager's tool calls |
| The manager answers without calling a worker | The prompt let it | Tell it that it knows nothing itself, and must ask first |
| `Stopped: no answer after 8 steps.` from a worker | The worker ran out of steps, and that text went to the manager as its answer | Read it as a failure, not an answer |
| A run shows no progress, with Ollama busy | A reply may be running away | Check that `num_predict` is set |
| A reply ends mid-sentence | It hit `LONGEST_REPLY` | Pass a bigger `num_predict` for that call |
| A batch of questions comes back as one vague answer | The search results overflowed the window | Use fewer questions, or a bigger window |
| A team's score is near zero, and the replies look right | Your check is too strict | Read the raw replies before you trust the score |

## Exercises

Open `exercises.py` in `chapters/30-multi-agent-systems`.

1. `worker_tool`: the heart of `agent_tool`. The check runs it in a real agent loop.
2. `pick_name`: the heart of `Router.pick`.
3. `count_copied`: count only the lines that really appear in a log.
4. `add_up`: split a job across logs, and keep the count in code.
5. `choose_architecture`: this chapter's chooser, in code.

Run this from that folder. These checks use a fake model, so Ollama doesn't need to run:

```bash
python3 -m pytest test_exercises.py
```

You've finished when you see `5 passed`. Worked answers are in [solutions/exercises.py](solutions/exercises.py).

**Exercise 6, optional: your own job.** Think of something you'd like an agent to do at work. Go through the five questions in
section 12, and write down your choice and why. Then build the simplest version, and measure it before you add anything.

## Common mistakes

- **Reaching for a team first.** Start with one agent. Split only when you can name what forced you to.
- **Comparing a team with an agent that did less.** Give the single agent the same steps and budget, or you're measuring the budget.
- **Deciding from one pass.** Ours tied at 17, and five passes showed a real gap.
- **Splitting documents that one search could cover.** You've created a decision, and the model can get it wrong.
- **Assuming the worker knows the chat.** It starts empty. Everything it needs must be in the task.
- **Letting the model add things up.** Workers miscounted even short logs. Add up in code.
- **Making pieces too big.** A team of 4 big workers did far worse than 48 small ones.
- **Trusting one total.** Our team hit the true total once, with every branch wrong.
- **Forgetting that limits multiply.** Eight steps inside eight steps isn't eight.
- **Treating a timeout as a limit on length.** A stream that keeps talking never times out.

## Recap

- An agent can be a tool for another agent. `agent_tool` is a few lines, and `Agent` didn't change.
- A worker starts with an empty chat, and the manager sees only its answer.
- A `Router` uses one model call to choose, then a worker does the whole job.
- On small questions, one agent scored 113 of 126. Real teams scored 92 to 102, with up to 2.3 times the calls.
- A perfect router only tied at 113. Splitting added a decision and gained nothing.
- Details weren't lost in handoffs here. Choosing was the weak point, and rewording only moved the mistakes around.
- On dependent steps, a relay got 93 of 150, one agent with two steps 75, and one agent 53. Part of a team's gain can just be extra
  work, and here a clean chat may be the rest. One pass tied, so we ran five.
- A fresh reviewer fixed 5 answers and broke 5.
- Twenty questions in one chat scored 0 of 20 past the window, with no error. One chat each got 93 of 108, and a bigger window got 83 in
  far fewer calls.
- On 48 logs, too big for any window, a team of small workers was the only setup that came close. It was still 3% to 46% off.
- Plain text search counted run-outs exactly. If code can do it, use code.
- A stream that never ends never times out, so every reply now has a length limit.

Start with one agent. Split only when you can name what forced you to, and then measure it.

## Where this comes from

The conditions in section 7 come from [Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296),
[Chain of Agents](https://research.google/blog/chain-of-agents-large-language-models-collaborating-on-long-context-tasks/),
[How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), and
[Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets](https://arxiv.org/abs/2604.02460).
The 7B study is [At Equal Inference Cost, Multi-Agent Structure Does Not Beat a Single Frozen Agent](https://arxiv.org/abs/2609.04217).
On debate and self-checking, see [Stop Overvaluing Multi-Agent Debate](https://arxiv.org/html/2502.08788v3) and
[Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/pdf/2310.01798). Two practical views are
[Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents) and
[Multi-Agents: What's Actually Working](https://cognition.com/blog/multi-agents-working). Vendor posts aren't peer-reviewed, and they report
their own systems.

**Next:** chapter 31 takes on security, where a split can earn its place for a different reason.
