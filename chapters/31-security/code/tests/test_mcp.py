import sys
from pathlib import Path

import pytest

from whitebox import Agent, FakeModel, McpClient, McpError, Message, ToolCall, Toolbox

SERVER = str(Path(__file__).parent / "fake_mcp_server.py")


def client(kind, timeout=5):
    return McpClient([sys.executable, SERVER, kind], timeout=timeout)


def test_a_new_server_uses_the_new_protocol():
    with client("new") as server:
        assert server.era == "new"


def test_an_old_server_falls_back_to_the_handshake():
    with client("old") as server:
        assert server.era == "old"
        assert server.call("double", {"number": 21}) == "42"


def test_tools_become_tools_an_agent_can_use():
    with client("new") as server:
        tools = server.tools()
        assert tools[0].name == "double"
        assert tools[0].description == "Double a number."
        model = FakeModel([Message("assistant", tool_calls=[ToolCall("double", {"number": 4})]), Message("assistant", "8")])
        result = Agent(model, Toolbox(tools)).run("Double 4")
        assert result.messages[-2].content == "8"


def test_a_tool_failure_comes_back_as_text():
    with client("new") as server:
        assert server.call("double", {"number": 0}) == "Error: Zero isn't allowed"


def test_a_stray_print_is_set_aside():
    with client("noisy") as server:
        assert server.call("double", {"number": 2}) == "4"
        assert "debug: got a request" in server.noise


def test_a_silent_server_times_out():
    with client("silent", timeout=1) as server:
        with pytest.raises(McpError, match="No reply"):
            server.tools()


def test_a_stopped_server_is_an_error():
    with client("dies") as server:
        with pytest.raises(McpError, match="stopped"):
            server.tools()


def test_a_failed_connect_stops_the_server():
    server = client("mute", timeout=1)
    with pytest.raises(McpError):
        server.__enter__()
    assert server.process.poll() is not None


def test_a_missing_program_is_an_mcp_error():
    with pytest.raises(McpError, match="Couldn't start"):
        McpClient(["no-such-program-here"])


def test_a_tool_with_no_properties_still_works_in_a_toolbox():
    with client("bare") as server:
        tool = server.tools()[0]
        assert Toolbox([tool]).check(tool, {"extra": 1}) == "Error: ping doesn't take extra"
