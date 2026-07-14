from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_tools import ToolContext, WorkspaceBoundaryError, read_file  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory)
    (workspace / "说明.md").write_text("第一行\n第二行\n", encoding="utf-8")
    context = ToolContext(workspace)
    assert read_file(context=context, path="说明.md", start_line=2) == "第二行\n"
    print("utf8=ok")
    try:
        read_file(context=context, path="../outside.md")
    except WorkspaceBoundaryError:
        print("outside=blocked")
