from pathlib import Path
import json
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_observability import Event, JsonlTraceWriter, validate_event_contract  # noqa: E402


events = [Event("run_started", 1, "run-1", 0), Event("run_completed", 2, "run-1", 1)]
validate_event_contract(events)
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "trace.jsonl"
    writer = JsonlTraceWriter(path)
    for event in events:
        writer(event)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    print(f"events={len(records)} sequences={[item['sequence'] for item in records]}")
