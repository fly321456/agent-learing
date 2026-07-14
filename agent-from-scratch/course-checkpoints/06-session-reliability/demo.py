from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from course_reliability import (  # noqa: E402
    CheckpointStore, ContextWindow, Message, RetryableError, RetryPolicy,
    RunCheckpoint, Session, SessionStore, execute_once,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        session = Session("demo")
        turn = session.start_turn("continue task")
        session.append_assistant(turn.id, "working")
        SessionStore(root / "sessions").save(session)

        context = ContextWindow(12).build([
            Message("user", "old context" * 3, "old"),
            Message("user", "new task", turn.id),
        ], summary="old work")

        checkpoint = RunCheckpoint("run-1", 2)
        writes: list[str] = []
        execute_once(checkpoint, "patch-1", lambda: writes.append("patched") or "ok")
        store = CheckpointStore(root / "checkpoints")
        store.save(checkpoint)
        restored = store.load("run-1")
        execute_once(restored, "patch-1", lambda: writes.append("duplicate") or "bad")

        attempts = 0
        def flaky() -> str:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RetryableError("temporary")
            return "recovered"

        result = RetryPolicy(2, 0).run(flaky)
        print(
            f"messages={len(session.messages)} context_trimmed={str(context.truncated).lower()} "
            f"side_effects={len(writes)} attempts={attempts} result={result}"
        )


if __name__ == "__main__":
    main()
