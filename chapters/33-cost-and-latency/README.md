# Chapter 33: Cost and latency

**Time:** about 2 hours. The long runs are optional, the cloud ones cost a few cents, and our results are saved. **You'll build:** a
`Meter` that records what each run costs in tokens, money and time, and a way to run questions at the same time.

## Where we are

Chapter 32 switched to a cloud model, put a key in `.env` and a spending limit in code. Every call now has a price, and some of them
took far longer than others. This chapter asks two plain questions about an agent run: where does the money go, and where does the
time go?

**The one new idea: measure each run, then decide what to cut.** You can't cut what you haven't measured, and some cuts cost more than
they save.

## Before you start

Activate the `.venv` you made in chapter 05, and work in `chapters/33-cost-and-latency/code`:

```bash
python3 -m pip install -r requirements.txt
```

[Start Ollama](../00-setup/README.md#step-4-start-ollama). The cloud scripts need the Gemini key from chapter 32, in `.env`. Every
cloud script here costs under a cent, except `many_at_once.py`, which cost us about two cents a run. Our results are in
`results/chapter33.json`, and `read_results.py` prints them.

`whitebox/meter.py` is new, and you'll read all of it. `Message` also gains `tokens_cached`, which `GeminiModel` fills in.
`models_setup.py` is provided, as in chapter 32. It builds the same agent, and now takes `k`, the number of search results, and `size`,
the number of words in each chunk.

To check the framework itself, run this from `code`:

```bash
python3 -m pytest tests
```

## 1. Measure one run

`Meter` is a hook, like chapter 16's `Tracer`. It times every model call, keeps its token counts, and adds up the time spent in tools:

```python
class Meter(Hook):
    """Records every model call. prices is (input, output) in dollars per million tokens, or None for a free model."""

    def __init__(self, prices=None, clock=time.perf_counter):
        self.prices = prices
        self.clock = clock
        self.steps = []
        self.tool_seconds = 0.0

    def before_model(self, messages):
        self.model_started = self.clock()

    def after_model(self, reply):
        seconds = round(self.clock() - self.model_started, 3)
        self.steps.append(Step(seconds, reply.tokens_in, reply.tokens_out, reply.tokens_cached))

    def before_tool(self, call):
        self.tool_started = self.clock()

    def after_tool(self, call, output):
        self.tool_seconds += self.clock() - self.tool_started

    def cost(self):
        """Dollars, at full price. Cached tokens may have cost less."""
        if not self.prices:
            return 0.0
        price_in, price_out = self.prices
        return sum(step.tokens_in * price_in + step.tokens_out * price_out for step in self.steps) / 1_000_000

    def report(self):
        lines = [f"{'Call':<6}{'Tokens in':>10}{'Out':>6}{'Cached':>8}{'Seconds':>9}"]
        for number, step in enumerate(self.steps, 1):
            lines.append(f"{number:<6}{step.tokens_in:>10,}{step.tokens_out:>6}{step.tokens_cached:>8}{step.seconds:>9.2f}")
        model_seconds = sum(step.seconds for step in self.steps)
        lines.append(f"Model {model_seconds:.2f} s, tools {self.tool_seconds:.2f} s, cost ${self.cost():.6f}")
        return "\n".join(lines)
```

`clock` is `time.perf_counter` unless you pass another, which is how the tests use a fake clock. [measure_one.py](code/measure_one.py)
asks one question with a `Meter` on the agent:

```bash
python3 measure_one.py ollama/qwen2.5:7b
python3 measure_one.py gemini/gemini-3.1-flash-lite
```

```text
$ python3 measure_one.py ollama/qwen2.5:7b
ollama/qwen2.5:7b: The initial till float amount is £150. [cash-handling.md]
Call   Tokens in   Out  Cached  Seconds
1            249    24       0     0.52
2            492    18       0     1.04
Model 1.56 s, tools 0.07 s, cost $0.000000
```

```text
$ python3 measure_one.py gemini/gemini-3.1-flash-lite
gemini/gemini-3.1-flash-lite: Each till starts the day with a float of £150. [cash-handling.md]
Call   Tokens in   Out  Cached  Seconds
1            173    18       0    34.79
2            413    21       0     1.47
Model 36.26 s, tools 0.10 s, cost $0.000205
```

Two calls each: one to choose the search, one to answer. The second call reads about twice as many tokens as the first, or more,
because it also carries the search results. And look at the cloud model's first call: **34.8 seconds**, for 18 tokens. A minute later, its second
call took 1.5. On another run, the same question took about 3 seconds in total. One run tells you little about time. You need several.

## 2. Where the tokens go

A model call sends the whole chat, every time. So what is in it? `where_tokens_go` splits what one call sends into its parts, by
characters:

```python
def where_tokens_go(messages, tools=()):
    """How many characters of each kind one model call sends. Characters, not tokens, but in the same proportion, roughly."""
    parts = {"system prompt": 0, "tool descriptions": 0, "question": 0, "tool results": 0, "model's own turns": 0}
    parts["tool descriptions"] = len(json.dumps([{"name": t.name, "description": t.description, "parameters": t.parameters} for t in tools]))
    for message in messages:
        if message.role == "system":
            parts["system prompt"] += len(message.content)
        elif message.role == "user":
            parts["question"] += len(message.content)
        elif message.role == "tool":
            parts["tool results"] += len(message.content)
        else:
            parts["model's own turns"] += len(message.content) + sum(len(c.name) + len(json.dumps(c.arguments)) for c in message.tool_calls)
    return parts
```

[where_tokens_go.py](code/where_tokens_go.py) runs one question and shows each call:

```bash
python3 where_tokens_go.py ollama/qwen2.5:7b
```

```text
$ python3 where_tokens_go.py ollama/qwen2.5:7b
Call       system prompt tool descriptions          question      tool results model's own turns
1                    398               282                47                 0                 0
2                    398               282                47             1,145                45
Share                30%               21%                4%               43%                2%
Characters, not tokens. A token is about four characters of English.
```

The system prompt and the tool descriptions go with every call, unchanged. Here's the same split across a whole pass of the eval:

```bash
python3 read_results.py breakdown
```

```text
$ python3 read_results.py breakdown
Share of everything sent, one pass of 42 questions
                            system      tools   question    results  own turns
qwen2.5:7b                     29%        20%         4%        43%         4%
gemini-3.1-flash-lite          17%        12%         2%        65%         3%
system = system prompt, tools = tool descriptions, results = tool results,
own turns = the model's earlier turns
qwen2.5:7b: model 117 s, tools 3 s, of 120 s
gemini-3.1-flash-lite: model 210 s, tools 8 s, of 218 s
```

**The question is the smallest part.** Search results are the biggest, at 43% on 7B and 65% on Flash-Lite, which searched more. The
system prompt and tool descriptions together are another 29% to 49%, sent again with every call.

The last two lines answer the time question too. The model took 117 of 120 seconds on 7B, and tools took 3. On this agent, time is model
time. Speeding up the search would save almost nothing.

## 3. Send less, and check the score

If search results are the biggest part, the obvious cut is fewer of them. `k` is how many results each search returns, 3 so far. `size`
is how many words go in each chunk, 60 so far. We ran the eval three times on each change:

```bash
python3 read_results.py less
```

```text
$ python3 read_results.py less
qwen2.5:7b, three passes of 42. k is search results per search, size is words per chunk
Setup             Right  Tokens in  Seconds
k=3, size 60     112/126   114,520      410
k=1, size 60      99/126    88,495      306
k=5, size 60     108/126   147,019      485
k=3, size 30     101/126   115,096      408
k=3, size 120    113/126   141,743      481
```

**Predict before you look at the rows:** fewer results means fewer tokens. Does it also mean a worse score?

- **One result per search** cut tokens by about a fifth, and the score from 112 to 99.
- **Smaller chunks** sent about the same tokens, because the model searched more often, and scored 101.
- **Five results** sent more and scored 108, no better than 3.
- **Bigger chunks** sent 24% more for 113, a point above 112. Runs vary by a few points, so that's a tie.

On 7B, the setting we already had was the right one. Every cut lost points.

### What a right answer costs

On a paid model, the question becomes money. Here's Flash-Lite, one pass each:

```bash
python3 read_results.py cost
```

```text
$ python3 read_results.py cost
gemini-3.1-flash-lite, one pass of 42, chunks of 60 words
Setup    Right  Tokens in     Cost  Per right answer
k=1      38/42     54,227  $0.0184         $0.000484
k=3      41/42     69,845  $0.0218         $0.000532
k=5      42/42    106,631  $0.0311         $0.000740
```

**Which is cheapest?** It depends what you divide by.

- **Per run**, one result is cheapest: $0.0184.
- **Per right answer**, one result is still cheapest: $0.000484, because it got 38 right for less.
- **Per question answered correctly every time**, only five results got all 42.

So which do you pick? If a wrong answer costs a customer, pay about $0.0003 more per right answer. If you're sorting a pile of emails and
a person checks them, take the cheap one. The measurement can't choose for you. It tells you the price of each choice.

## 4. Where the time goes

Section 2 showed that time is model time. Two things about model time matter.

**When do the first words arrive?** A person waiting for an answer feels the first words, not the last.
[first_words.py](code/first_words.py) streams one short answer, and times both:

```bash
python3 first_words.py ollama/qwen2.5:7b
python3 first_words.py gemini/gemini-3.1-flash-lite
```

```text
$ python3 first_words.py ollama/qwen2.5:7b
Try   First words  Whole reply
1           0.21s        1.24s
2           0.02s        1.36s
3           0.03s        0.88s
```

```text
$ python3 first_words.py gemini/gemini-3.1-flash-lite
Try   First words  Whole reply
1           1.95s        1.95s
2           2.12s        2.12s
3           1.29s        1.29s
```

On 7B, the first words arrive in a few hundredths of a second, after the first try, which loads the model. On Flash-Lite, the first
words and the whole reply arrive together. That's not Gemini, that's us: chapter 32's `GeminiModel` has no `stream`, so it falls back to
the `Model` default, which waits for the whole reply and hands it over in one piece. Gemini has a streaming endpoint,
`streamGenerateContent`, that we didn't write. If people watch your agent answer, that's worth writing.

**How much does it vary?** Here are our saved runs:

```bash
python3 read_results.py stream
```

```text
$ python3 read_results.py stream
Model                    First words  Whole reply
qwen2.5:7b                     1.00s        1.80s
qwen2.5:7b                     0.03s        0.86s
qwen2.5:7b                     0.03s        1.06s
gemini-3.1-flash-lite          5.77s        5.77s
gemini-3.1-flash-lite          1.68s        1.68s
gemini-3.1-flash-lite         17.47s       17.47s
```

Answers of 55 to 59 tokens took 1.7 seconds once and 17.5 seconds another time. That spread is one reason chapter 17 added timeouts and
retries, and it's why one timing proves nothing.

## 5. Many at once

An agent spends almost all of its time waiting for the model. On a cloud model, that waiting happens on Google's computers, so you can
wait for several at once. `run_many` runs each question on its own new agent, several at a time:

```python
def run_many(make_agent, questions, workers=4):
    """Run each question on its own new agent, several at a time.

    Results come back in the order of the questions, whatever order they finish in.
    """
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(lambda question: make_agent().run(question), questions))
```

Why a new agent each time? Because hooks keep state. `LoopGuard` counts the calls in a run, and two runs sharing one `LoopGuard`
would count each other's calls. `pool.map` returns the results in the order of the questions, whatever order they finish in.

**Predict:** with 8 at once, how much faster is the cloud model? And the model on your own computer?

```bash
python3 read_results.py parallel
```

```text
$ python3 read_results.py parallel
Model                    At once  Right  Seconds
qwen2.5:7b                     1  38/42      147
qwen2.5:7b                     4  36/42      147
qwen2.5:7b                     8  37/42      135
gemini-3.1-flash-lite          1  40/42      447
gemini-3.1-flash-lite          4  41/42       96
gemini-3.1-flash-lite          8  40/42       64
```

- **Flash-Lite: 447 seconds became 64**, about 7 times faster, with the same score. Its single-file run was slow that time. On another
  day, chapter 32's took 244.
- **7B: 147 seconds became 135.** Almost nothing. Ollama on one Mac seemed to answer one request at a time here, so the questions
  just queued.

Running at the same time saves time, not money. The same tokens are sent either way. And a provider limits how many requests you can
send per minute, so at some number of workers you'll start getting 429 errors. Our `Retry` waits and tries again, but that's lost time.

To try it, [many_at_once.py](code/many_at_once.py) runs the 42 questions:

```bash
python3 many_at_once.py gemini/gemini-3.1-flash-lite 8
```

## 6. Caching, when it happens

The system prompt and tool descriptions are the same in every call. Google can keep the start of a prompt it has just seen, and charge
less when you send it again. That's called caching. Google's [caching docs](https://aistudio.google.com/docs/caching.md?generate-content=true)
say it's on by default for Gemini 2.5 and newer models, and that on some models, 3.6 Flash among them, a prompt needs at least 4,096
tokens. Cached input costs a tenth of the normal price, by the [pricing page](https://aistudio.google.com/docs/pricing).

So we sent chapter 30's 40 long tools, 6,569 tokens, five times in a row, and read how many tokens Google said came from its cache:

```bash
python3 read_results.py cache
```

```text
$ python3 read_results.py cache
The 40 tools from chapter 30, 6,569 tokens, sent five times
Model                   From cache, each try          
gemini-3.1-flash-lite   0  0  3,977  3,977  3,977
gemini-3.6-flash        0  0  0  0  0
```

Flash-Lite started caching on the third try. 3.6 Flash never did, although its prompt was well over 4,096 tokens. Then
[cache_check.py](code/cache_check.py) sent the whole handbook, 4,869 tokens, five times:

```bash
python3 cache_check.py gemini/gemini-3.1-flash-lite
python3 cache_check.py gemini/gemini-3.6-flash
```

```text
$ python3 cache_check.py gemini/gemini-3.1-flash-lite
Try   Tokens in  From cache  Cost if none cached       Cost
1         4,869       2,033            $0.001231  $0.000773
2         4,869       2,033            $0.001231  $0.000773
3         4,869       2,033            $0.001231  $0.000773
4         4,869       2,033            $0.001231  $0.000773
5         4,869       2,033            $0.001231  $0.000773
Cached input costs a tenth of the normal price on both models here, by Google's pricing page.
```

```text
$ python3 cache_check.py gemini/gemini-3.6-flash
Try   Tokens in  From cache  Cost if none cached       Cost
1         4,869           0            $0.005309  $0.005309
2         4,869           0            $0.005317  $0.005317
3         4,869           0            $0.005197  $0.005197
4         4,869           0            $0.005298  $0.005298
5         4,869           0            $0.006078  $0.006078
Cached input costs a tenth of the normal price on both models here, by Google's pricing page.
```

This time Flash-Lite cached from the first try, because we'd sent the same prompt a few minutes earlier, while writing this chapter.
Each call cost 37% less. 3.6 Flash again cached nothing.

**So caching helps when it happens, and you can't count on it.** The docs describe when it may happen, not that it will. What you can
do is make it likely: keep the parts that never change, the system prompt and the tool descriptions, at the start, and the same, byte
for byte. Google's docs advise putting "large and common contents at the beginning". Then read `tokens_cached` to see whether it worked.

Our `SpendLimit` still counts cached tokens at the full price. That can only overstate what you spent, which is the safe way to be wrong.

## 7. What to cut

Here's what this chapter measured, as a short list:

1. **Measure first.** Put a `Meter` on the agent and run your eval. Find the biggest part, in tokens and in seconds.
2. **Check every cut against the eval.** Fewer search results saved tokens and lost points on both models.
3. **Count cost per right answer, not per call.** A cheaper call that's wrong more often may not be cheaper.
4. **For time, look at the model first.** Here it was 97% of the time. Run questions at the same time on a cloud model, and stream
   when people are watching.
5. **Keep the start of every prompt the same,** so caching can happen, and check whether it did.

## What this does and doesn't show

- One Mac with 24 GB, Ollama 0.34.4, temperature 0.7, and Google's API on 8 November 2026, on the paid tier. Times on the cloud varied
  by ten times within the same hour.
- Local rows are three passes of 42 questions, cloud rows one pass. Runs vary by a few points, so small differences are noise.
- The shares in section 2 are characters, not tokens. A token is about four characters of English, so the proportions are close.
- Caching was a few tries on two models on one day. It's not a promise either way.
- Ollama seemed to answer one request at a time on our Mac. Its settings, and other machines, can change that.
- We didn't measure how many requests per minute Google allows. Too many workers will meet that limit.

## Reading errors

| What you see | What it means | What to do |
|---|---|---|
| One call takes 30 seconds, the next takes 1 | Normal variation on a cloud model | Measure several runs before you decide anything |
| `Gemini said 429: ...` with many workers | Too many requests in a short time | Use fewer workers. `Retry` waits, but that's lost time |
| A run's answers come back mixed up | You shared one agent between threads | Make a new agent for each question, as `run_many` does |
| `From cache` is always 0 | The provider didn't cache, or the prompt is too short | Keep the start of the prompt identical, and accept that it may not happen |
| First words arrive with the whole reply | That model class has no `stream` | Write `stream` for it, or accept the wait |
| The score drops after a cut | You sent the model too little | Undo it. A cut that loses points isn't a saving |

## Exercises

Open `exercises.py` in `chapters/33-cost-and-latency`.

1. `shares`: turn character counts into shares of the total.
2. `cost_per_right`: what each right answer cost.
3. `cached_cost`: the cost of a reply when some input came from the cache.
4. `ModelTimer`: the heart of `Meter`, as a hook.
5. `run_all`: the heart of `run_many`.

Run this from that folder. These checks use a fake model, so Ollama doesn't need to run, and there's no key:

```bash
python3 -m pytest test_exercises.py
```

Before you start, it looks like this:

```text
$ python3 -m pytest test_exercises.py
FAILED test_exercises.py::test_todo_1_shares - AssertionError: assert None ==...
FAILED test_exercises.py::test_todo_2_cost_per_right - assert None == 0.000484
FAILED test_exercises.py::test_todo_3_cached_cost - assert None == 0.001222
FAILED test_exercises.py::test_todo_4_model_timer - assert [] == [2.5, 1.0]
FAILED test_exercises.py::test_todo_5_run_all - AssertionError: assert None =...
============================== 5 failed in 0.05s ===============================
```

You've finished when you see `5 passed`. Worked answers are in [solutions/exercises.py](solutions/exercises.py).

**Exercise 6, optional: your biggest part.** Put a `Meter` and `where_tokens_go` on your own agent. Find its biggest part, change one
thing, and run your eval before and after.

## Common mistakes

- **Cutting before measuring.** Here, the question was 4% of what we sent. Shortening it would have saved nothing.
- **Judging a cut by tokens alone.** Fewer search results saved over a fifth of the tokens, and lost 13 points.
- **Dividing by calls, not by right answers.** The cheapest call isn't always the cheapest answer.
- **Timing one run.** The same call took 1.7 seconds and 17.5 seconds.
- **Speeding up the tools.** They were 3% of the time here.
- **Sharing one agent between threads.** Hooks keep state, so each question needs its own.
- **Counting on caching.** Check `tokens_cached`. One model here never cached at all.

## Recap

- `Meter` records the tokens and time of every model call, and the time in tools. `where_tokens_go` splits what each call sends.
- Search results were the biggest part, then the system prompt and tool descriptions, sent again every call. The question was 2% to 4%.
- The model was 97% of the time on 7B. Tools were 3%.
- Fewer search results cut tokens by about a fifth, and lost points on both models.
- Per right answer, one search result was cheapest on Flash-Lite, and only five got every question right. The price of each choice
  is measurable. The choice is yours.
- Our `GeminiModel` doesn't stream, so its first words wait for the whole reply. The same reply took 1.7 to 17.5 seconds.
- Eight questions at once made the cloud eval about 7 times faster, and did almost nothing on one Mac.
- Flash-Lite cached part of a repeated prompt, and charged 37% less. 3.6 Flash never cached.

Measure each run, then decide what to cut.

## Where this comes from

Caching is described in Google's [context caching docs](https://aistudio.google.com/docs/caching.md?generate-content=true), and prices,
including cached input, on the [pricing page](https://aistudio.google.com/docs/pricing). The streaming endpoint is in the
[API reference](https://aistudio.google.com/api-reference/generate-content/stream-generate-content.md). Python's
[`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html) documentation covers `ThreadPoolExecutor`.

**Next:** finish the [Part 7 checkpoint](../../checkpoints/part-7/README.md), which puts chapters 30 to 33 together, then start Part 8.
