# Whitebox: Build an AI Agent from Scratch

A [Whitebox Academy](https://www.youtube.com/@WhiteboxAcademy) course. Open the black box.

A self-paced course. You start with basic Python and finish with your own agent
framework and a coding agent that fixes bugs on its own. No experience with LLMs,
RAG, agents or MCP is needed.

The course has 35 chapters and takes about 85 hours.

## How to take the course

1. Follow [SETUP.md](SETUP.md).
2. Work through [ROADMAP.md](ROADMAP.md) in order. Each chapter builds on the last.
3. In each chapter, watch the video, read the article, then run the exercises.
4. Pass the checkpoint at the end of each part before moving on.

Stuck? Start with [docs/troubleshooting.md](docs/troubleshooting.md).

## Why a small model

This course runs `qwen2.5:7b` on your own computer, so anyone can take it without paying for an API.
A bigger model may give better results. The concepts, the code and the framework you build stay the
same, and you can switch models whenever you like. Chapter 32 switches models, first to a bigger one on your computer, then to Gemini in the cloud.

The numbers won't stay the same. Every score in the course comes from real runs of this one model, so
a stronger model may score higher, and some failures we show may shrink or disappear. That's why you
learn to measure: run the evals on your own model and trust those numbers.

## What's in a chapter

```text
chapters/12-agent-loop/
├── README.md       the lesson
├── code/           the complete code as of this chapter
├── exercises.py    exercises that check themselves
└── solutions/      worked answers
```

If you fall behind or break something, you can continue from the next chapter's
`code/` folder.

## Getting the code

You don't need to know Git or have a GitHub account. Open this repo on GitHub and
choose **Code > Download ZIP**.

## License

The code is under the [MIT License](LICENSE). The articles and videos are under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): you can reuse them with credit.
