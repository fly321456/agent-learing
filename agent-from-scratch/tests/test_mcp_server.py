from __future__ import annotations

import anyio
import pytest

pytest.importorskip("mcp")

from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

from agent_from_scratch.mcp_server import create_server


def test_read_only_mcp_server_over_in_memory_transport(tmp_path):
    (tmp_path / "README.md").write_text("course marker\n", encoding="utf-8")

    async def scenario() -> None:
        server = create_server(tmp_path)
        async with create_connected_server_and_client_session(server) as client:
            listed = await client.list_tools()
            assert {tool.name for tool in listed.tools} == {
                "read_workspace_file",
                "search_workspace",
            }

            result = await client.call_tool(
                "read_workspace_file",
                {"path": "README.md"},
            )
            assert result.isError is False
            assert isinstance(result.content[0], TextContent)
            assert "course marker" in result.content[0].text

            denied = await client.call_tool(
                "read_workspace_file",
                {"path": "../outside.txt"},
            )
            assert denied.isError is True

    anyio.run(scenario)
