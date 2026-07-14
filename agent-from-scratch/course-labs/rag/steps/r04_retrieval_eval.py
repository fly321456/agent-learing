from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_lab import recall_at_k  # noqa: E402

score = recall_at_k([["a", "b"], ["x", "c"], ["z"]], [{"a"}, {"c"}, {"missing"}], 2)
print(f"queries=3 recall_at_2={score:.3f}")
