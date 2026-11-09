"""Chapter 34's coding agent in Pydantic AI 2.66.0."""
import functools
import os

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # otherwise every run prints an advert for its paid service

from pydantic_ai import Agent, ModelRetry, UsageLimits
from whitebox import load_env
from whitebox.coding import CODING_SYSTEM, coding_tools


def retry_on_error(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ValueError as error:
            raise ModelRetry(str(error)) from error  # without it, a tool's error ends the run
    return wrapped


def model_for(spec):
    provider, name = spec.split("/", 1)
    if provider == "ollama":
        from pydantic_ai.models.ollama import OllamaModel
        from pydantic_ai.providers.ollama import OllamaProvider
        ollama = OllamaProvider(base_url="http://localhost:11434/v1")
        # Send the reply limit as max_tokens, because Ollama ignores max_completion_tokens.
        # And leave out the <system> note, which led 14B to invent bug reports.
        profile = {**ollama.model_profile(name),
                   "openai_chat_supports_max_completion_tokens": False,
                   "supports_inline_system_prompts": True}
        return OllamaModel(name, provider=ollama, profile=profile)
    from pydantic_ai.models.google import GoogleModel
    from pydantic_ai.providers.google import GoogleProvider
    load_env()
    return GoogleModel(name, provider=GoogleProvider(api_key=os.environ["GEMINI_API_KEY"]))


def coding_agent(folder, spec="ollama/qwen2.5:7b", max_tokens=1024):
    tools = [retry_on_error(tool.function) for tool in coding_tools(folder)]
    return Agent(model_for(spec), system_prompt=CODING_SYSTEM, tools=tools,
                 retries=15,  # the default ends a run on a tool's second error
                 model_settings={"temperature": 0.7, "max_tokens": max_tokens})


def fix(folder, question, spec="ollama/qwen2.5:7b", max_tokens=1024):
    return coding_agent(folder, spec, max_tokens).run_sync(question, usage_limits=UsageLimits(request_limit=15)).output
