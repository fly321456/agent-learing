from rag_lab import (
    Document, InvertedIndex, chunk_document, format_retrieved_context, recall_at_k,
)

documents = [
    Document("server.md", "Acme server uses port 4312 for local development."),
    Document("client.md", "Acme client reads the server URL from configuration."),
]
chunks = [chunk for document in documents for chunk in chunk_document(document, 80, 10)]
results = InvertedIndex(chunks).search("Acme server port", top_k=2)
context = format_retrieved_context(results)
score = recall_at_k([[result.chunk.source for result in results]], [{"server.md"}], 1)
print(f"chunks={len(chunks)} retrieved={len(results)} top={results[0].chunk.source}")
print(f"source_guard={str('UNTRUSTED' in context).lower()} recall_at_1={score:.1f}")
