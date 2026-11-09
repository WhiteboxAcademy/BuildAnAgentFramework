# The box the coding agent's code runs in: Python and pytest, nothing else.
FROM python:3.14-slim
RUN pip install --no-cache-dir pytest==9.2.0
RUN useradd --create-home runner
USER runner
WORKDIR /work
