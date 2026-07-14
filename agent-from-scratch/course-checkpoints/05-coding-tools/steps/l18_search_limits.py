from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_tools import ToolContext, search_files  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory)
    (workspace / "app.py").write_text("TODO one\nTODO two\nTODO three\n", encoding="utf-8")
    output = search_files(context=ToolContext(workspace), query="TODO", glob="*.py", max_results=2)
    print(output)
