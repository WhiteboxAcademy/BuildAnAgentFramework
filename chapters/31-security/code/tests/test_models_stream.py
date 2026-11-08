import pytest
import requests

from whitebox import Message, ModelError, OllamaModel


class Broken:
    ok = True

    def iter_lines(self):
        yield b'{"message": {"content": "Hel"}}'
        raise requests.ConnectionError("read timed out")


def test_a_lost_connection_mid_reply_becomes_a_model_error(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: Broken())
    with pytest.raises(ModelError) as caught:
        list(OllamaModel("test").stream([Message("user", "Hi")]))
    assert caught.value.retryable
