from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_lab import answer_without_retrieval  # noqa: E402

print(f"baseline={answer_without_retrieval('What port does Acme use?')}")
