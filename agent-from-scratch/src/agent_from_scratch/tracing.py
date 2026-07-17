import json
from pathlib import Path

from .redaction import sanitize_for_logging
from .schemas import Event


class JsonlTraceWriter:
    def __init__(self, path: Path):
        self.path = Path(path)

    def __call__(self, event: Event) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = event.to_dict()
        record["data"] = sanitize_for_logging(record["data"])
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
