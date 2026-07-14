from pathlib import Path
import tomllib


root = Path(__file__).resolve().parents[1]
project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
print(f"package={project['name']} version={project['version']} python={project['requires-python']}")
print("release_checks=tests,wheel,editable,cli,mcp,readme")
