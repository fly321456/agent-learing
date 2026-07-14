import asyncio
from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from course_product import Event, create_mcp_server, format_event, request_approval  # noqa: E402


def main() -> None:
    event = Event("tool_called", 1, "run-1", 1, {"name": "read_workspace_file"})
    with tempfile.TemporaryDirectory() as directory:
        server = create_mcp_server(Path(directory))
        tools = asyncio.run(server.list_tools())
    approved = request_approval("run_command", {}, lambda _prompt: "no")
    print(format_event(event))
    print(
        f"approval_default={str(approved).lower()} mcp_transport=stdio "
        f"mcp_tools={len(tools)} final_project=ready"
    )


if __name__ == "__main__":
    main()
