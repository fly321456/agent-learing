import os
from pathlib import Path

from .tools import ToolContext, read_file, search_files


def create_server(workspace: Path):
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install the 'mcp' extra: pip install -e .[mcp]") from exc

    root = Path(workspace).resolve()
    context = ToolContext(workspace=root)
    server = FastMCP("Coding Agent Read-Only Workspace")

    @server.tool()
    def read_workspace_file(path: str, start_line: int = 1, end_line: int | None = None) -> str:
        """Read UTF-8 text from a path inside the configured workspace."""
        return read_file(
            context=context,
            path=path,
            start_line=start_line,
            end_line=end_line,
        )

    @server.tool()
    def search_workspace(query: str, path: str = ".", glob: str = "*") -> str:
        """Search UTF-8 files inside the configured workspace."""
        return search_files(context=context, query=query, path=path, glob=glob)

    return server


def main() -> None:
    workspace = Path(os.getenv("AGENT_WORKSPACE", "."))
    create_server(workspace).run()


if __name__ == "__main__":
    main()

