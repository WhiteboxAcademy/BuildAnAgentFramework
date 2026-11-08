# Troubleshooting

## "could not connect to ollama server" or "Connection refused"

Ollama isn't running. See [how to start Ollama](../chapters/00-setup/README.md#step-4-start-ollama).

## "model not found"

Download the model with `ollama pull qwen2.5:7b`.

## A run seems frozen, and Ollama is busy

Rarely, the model starts repeating itself and never stops. A timeout can't catch this, because the reply keeps arriving. Press
Ctrl+C and run it again. To stop it happening, pass `num_predict=1024` in your options, or `"num_predict": 1024` in `OPTIONS` in
`library.py`. Chapter 30 explains this, and from that chapter on `OllamaModel` sets a limit for you.

## `KeyError: 'message'` from `whitebox/models.py`

Rarely, Ollama sends an error partway through a streamed reply. In chapters 15 to 29, and checkpoints 3 to 6, `OllamaModel.stream`
expects every line to hold a message, so it crashes with `KeyError: 'message'` instead of saying what went wrong. It isn't a bug in
your code. Run it again. If it keeps happening, check that Ollama is running and that your computer has enough free memory for the
model.

From chapter 30 on, `OllamaModel` turns that line into a `ModelError`, which `Retry` already handles. To get the same in an earlier
chapter, add these two lines to `stream` in `whitebox/models.py`, straight after `data = json.loads(line)`:

```python
                if "error" in data:
                    raise ModelError(f"Ollama said: {data['error']}", retryable=True)
```
