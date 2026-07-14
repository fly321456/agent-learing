from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_lab import Document, InvertedIndex, chunk_document  # noqa: E402

chunks = chunk_document(Document("guide.md", "Acme server uses port 4312."), 20, 5)
results = InvertedIndex(chunks).search("Acme port", 2)
print(f"chunks={len(chunks)} top_source={results[0].chunk.source} score={results[0].score}")
