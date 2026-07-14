from __future__ import annotations

from pathlib import Path
from typing import Callable


def _workspace_path(workspace: Path, path: str) -> Path:
    target = (workspace / path).resolve()
    try:
        target.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"Path is outside the workspace: {path}") from exc
    return target


def create_read_only_tools(workspace: Path) -> dict[str, Callable]:
    root = Path(workspace).resolve()

    def read_workspace_file(path: str, start_line: int = 1, end_line: int | None = None) -> str:
        target = _workspace_path(root, path)
        text = target.read_text(encoding="utf-8", errors="strict")
        return "".join(text.splitlines(keepends=True)[start_line - 1:end_line])

    def search_workspace(
        query: str, path: str = ".", glob: str = "*", max_results: int = 50,
    ) -> str:
        search_root = _workspace_path(root, path)
        matches: list[str] = []
        for candidate in sorted(search_root.rglob(glob)):
            if not candidate.is_file() or ".git" in candidate.parts:
                continue
            try:
                lines = candidate.read_text(encoding="utf-8", errors="strict").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for line_number, line in enumerate(lines, start=1):
                if query in line:
                    relative = candidate.relative_to(root).as_posix()
                    matches.append(f"{relative}:{line_number}:{line}")
                    if len(matches) >= max_results:
                        return "\n".join(matches) + "\n... [result limit reached]"
        return "\n".join(matches)

    return {
        "read_workspace_file": read_workspace_file,
        "search_workspace": search_workspace,
    }


def create_mcp_server(workspace: Path):
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install the mcp extra to create the server") from exc

    tools = create_read_only_tools(workspace)
    server = FastMCP("Course Read-Only Coding Tools")
    server.tool()(tools["read_workspace_file"])
    server.tool()(tools["search_workspace"])
    return server
