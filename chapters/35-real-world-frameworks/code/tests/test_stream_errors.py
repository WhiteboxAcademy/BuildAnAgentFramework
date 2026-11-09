import pytest
import requests

from whitebox import Message, ModelError, OllamaModel


class SaysError:
    ok = True

    def iter_lines(self):
        yield b'{"error": "the runner stopped"}'


def test_an_error_line_in_a_stream_becomes_a_model_error(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: SaysError())
    with pytest.raises(ModelError, match="the runner stopped") as caught:
        list(OllamaModel("test").stream([Message("user", "Hi")]))
    assert caught.value.retryable
