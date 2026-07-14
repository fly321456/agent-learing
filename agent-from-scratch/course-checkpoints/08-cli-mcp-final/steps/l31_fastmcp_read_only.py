import asyncio
from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_product import create_mcp_server  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    server = create_mcp_server(Path(directory))
    tools = asyncio.run(server.list_tools())
    print(f"transport=stdio tools={','.join(sorted(tool.name for tool in tools))}")
