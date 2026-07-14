from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_reliability import Session, SessionStore  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    session = Session("learning")
    turn = session.start_turn("inspect repository")
    session.append_assistant(turn.id, "ready")
    store = SessionStore(Path(directory))
    store.save(session)
    restored = store.load("learning")
    print(f"session={restored.id} turns=1 messages={len(restored.messages)}")
