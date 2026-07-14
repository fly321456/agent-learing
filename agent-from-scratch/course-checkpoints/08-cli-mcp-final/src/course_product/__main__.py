from pathlib import Path

from .mcp_server import create_mcp_server


def main() -> None:
    create_mcp_server(Path.cwd()).run()


if __name__ == "__main__":
    main()
