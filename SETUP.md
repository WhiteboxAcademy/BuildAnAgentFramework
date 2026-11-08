# Setup

You'll need about 10 GB of free disk space and at least 8 GB of memory.

## 1. Install Python

Install Python 3.12 or newer from [python.org](https://www.python.org/downloads/).
On Windows, tick **Add python.exe to PATH** on the first install screen.

## 2. Install Ollama

Ollama runs AI models on your own computer. Install it from
[ollama.com/download](https://ollama.com/download), then
[start it](chapters/00-setup/README.md#step-4-start-ollama). Next, download the course model
(about 5 GB):

```bash
ollama pull qwen2.5:7b
```

## 3. Create your Python environment

From the course folder:

```bash
# macOS and Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

## Added later in the course

You don't need these yet:

- **Docker**, from chapter 34.
- **A Gemini API key**, from chapter 32. Copy `.env.example` to `.env` and add it there.
