from app.services.embedding_service import (
    generate_embeddings,
    get_embedding_dimension
)

chunks = [
    {
        "chunk_id": "test-001",
        "chunk_index": 0,
        "page_number": 1,
        "text": "Machine learning enables computers to learn from data."
    },
    {
        "chunk_id": "test-002",
        "chunk_index": 1,
        "page_number": 1,
        "text": "Neural networks are computational models inspired by the brain."
    }
]

embeddings = generate_embeddings(chunks)

print("Embedding dimension:", get_embedding_dimension())
print("Total embeddings:", len(embeddings))

for item in embeddings:
    print("Chunk ID:", item["chunk_id"])
    print("Vector length:", len(item["embedding"]))