"""MCP: use tools that live in another program, over the Model Context Protocol."""
import json
import queue
import subprocess
import threading

from .tools import Tool

KEY = "io.modelcontextprotocol/"
NEW, OLD = "2026-07-28", "2025-06-18"
ME = {"name": "whitebox", "version": "1"}


class McpError(Exception):
    pass


class McpClient:
    """Start a server as a separate program, and talk to it with one line of JSON each way."""

    def __init__(self, command, cwd=None, timeout=30):
        self.timeout = timeout
        self.number = 0
        self.era = None
        self.noise = []  # Lines the server wrote that weren't JSON, such as a stray print.
        self.lines = queue.Queue()
        try:
            self.process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        except OSError as error:
            raise McpError(f"Couldn't start the server: {error}") from error
        threading.Thread(target=self.read_lines, daemon=True).start()

    def read_lines(self):
        """Runs beside the main program, so a silent server can't freeze it."""
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def __enter__(self):
        try:
            self.connect()
        except McpError:
            self.close()  # __exit__ doesn't run if __enter__ fails, so don't leave the server running.
            raise
        return self

    def __exit__(self, *details):
        self.close()

    def close(self):
        self.process.terminate()
        try:
            self.process.stdin.close()
        except OSError:
            pass  # The server has already gone, so there's nothing left to flush.
        self.process.wait(timeout=5)

    def send(self, message):
        try:
            self.process.stdin.write(json.dumps(message) + "\n")
            self.process.stdin.flush()
        except OSError as error:
            raise McpError(f"The server has stopped: {error}") from error

    def reply_to(self, number):
        """Wait for the reply to one request, skipping anything else the server says."""
        while True:
            try:
                line = self.lines.get(timeout=self.timeout)
            except queue.Empty:
                raise McpError(f"No reply after {self.timeout} seconds") from None
            if line is None:
                raise McpError("The server has stopped")
            try:
                message = json.loads(line)
            except ValueError:
                self.noise.append(line.strip())
                continue
            if isinstance(message, dict) and message.get("id") == number:
                return message

    def ask(self, method, **params):
        """Send one request and return the whole reply."""
        self.number += 1
        if self.era != "old":
            params["_meta"] = {KEY + "protocolVersion": NEW, KEY + "clientCapabilities": {}, KEY + "clientInfo": ME}
        self.send({"jsonrpc": "2.0", "id": self.number, "method": method, "params": params})
        return self.reply_to(self.number)

    def result(self, method, **params):
        reply = self.ask(method, **params)
        if "error" in reply:
            raise McpError(f"{method}: {reply['error'].get('message')}")
        return reply["result"]

    def connect(self):
        """Use the new protocol if the server offers it. Any other answer means use the old handshake."""
        reply = self.ask("server/discover")
        if NEW in reply.get("result", {}).get("supportedVersions", []):
            self.era = "new"
            return
        self.era = "old"
        self.result("initialize", protocolVersion=OLD, capabilities={}, clientInfo=ME)
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def tools(self):
        """Return the server's tools, as Tools an Agent can use."""
        return [self.as_tool(item) for item in self.result("tools/list")["tools"]]

    def as_tool(self, item):
        schema = {"properties": {}, "required": [], **item["inputSchema"]}
        name = item["name"]

        def run(**arguments):
            return self.call(name, arguments)

        return Tool(name, item.get("description", ""), schema, run)

    def call(self, name, arguments):
        """Run one tool on the server, and return its text. A tool's failure comes back as text the model can read."""
        result = self.result("tools/call", name=name, arguments=arguments)
        text = "\n".join(part.get("text", "") for part in result["content"])
        return f"Error: {text}" if result.get("isError") else text
