import json
from pathlib import Path

from .schemas import Event


class JsonlTraceWriter:
    def __init__(self, path: Path):
        self.path = Path(path)

    def __call__(self, event: Event) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

