# Your final project

You've built an agent framework, a coding agent, and tested real frameworks against it. Now build something of your own.

## Roll for an idea

Type your name, roll two dice, and get one project idea. Each idea comes with a harder version, a real improvement to build once the
first version works, and the twists that fit it. The time you roll is part of it too, so every roll is different, and the roll shows
its time so you can see it again. You can roll on the [course
page](https://whiteboxacademy.in/courses/build-an-ai-agent/final-project/), or here:

```bash
python3 roll.py "Your Name" 3 5
```

You can choose a level first, and the roll picks only from the ideas at that level:

- **Starter:** one agent, a few tools or a search, and a short run.
- **Intermediate:** more moving parts: memory, state that lasts, the sandbox or MCP.
- **Advanced:** several agents, limits enforced in code, or careful measurement.

```bash
python3 roll.py "Your Name" 3 5 starter
```

There are 58 ideas, from answering questions about your own notes to a team of agents running a small business. Rolling is part of
the fun, so the page shows only yours. The list isn't secret: it's in [projects.json](projects.json), if you'd rather choose. You
can also skip the dice and build your own idea.

Build the first version, then the harder version if you have time. The twists are about how your agent behaves, not what it does:
keep working when a tool fails, resist a planted attack, pick up after a restart, compare two frameworks or two models, say "I don't
know", stop at a budget, or split the work between a builder and a checker. Each idea lists only the twists that make sense for it.
Take one, several, or none.

## The rules

- **A weekend's work.** Small and finished beats big and half-done.
- **Works on `qwen2.5:7b`,** so anyone can run it for free. A cloud model is fine as well.
- **Free:** no paid service, no sign-up.
- **No one else's personal data.** Use your own, or make some up.
- **Build it with any framework from the course:** whitebox, LangGraph or Pydantic AI.
- **Write an eval,** as in chapter 18, and report what your agent used: tokens and time, and cost on a cloud model. No twist sets a
  number for you to hit. Measure, and say what you found.

## Share it, if you like

Sharing is optional, and each step has its own place in the course's
[Discussions](https://github.com/WhiteboxAcademy/BuildAnAgentFramework/discussions):

- **Your roll** goes in
  [Final projects](https://github.com/WhiteboxAcademy/BuildAnAgentFramework/discussions/categories/final-projects). On the course
  page, tick the box to record it, and the page fills in your entry for you to post.
- **Your own idea** goes in [Ideas](https://github.com/WhiteboxAcademy/BuildAnAgentFramework/discussions/categories/ideas).
  Describe it the way the course's ideas are described: what it does, a harder version, the chapters it uses, what your eval will
  check, and its level. The course page has a form for this too.
- **When it's built, show it** in a new discussion in
  [Show and tell](https://github.com/WhiteboxAcademy/BuildAnAgentFramework/discussions/categories/show-and-tell): a link to your
  code, your eval's result, what it used, and what didn't work. That last part is often the most useful. Link it to your roll or
  idea.

The page never posts anything itself. You post from your own GitHub account, and only if you want to.

## How the roll works

`roll.py` lower-cases your name, tidies its spaces, and hashes it with the time and the two dice using SHA-256, as
`name|time|first|second`. The time is UTC, to the second, such as `2026-11-09T14:32:07Z`. The first four bytes of the hash pick the
idea, from the ideas at your level if you chose one. The course page does the same in your browser, and sends nothing anywhere.

Each roll prints its time. Give that time back with `--at`, and you get the same project again:

```bash
python3 roll.py "Your Name" 3 5 starter --at 2026-11-09T14:32:07Z
```

`test_roll.py` pins seven rolls at a fixed time, so the page and this script must always agree.
