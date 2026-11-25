
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import (
    store_embeddings,
    search_similar_chunks,
    get_vector_count
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

# Generate embeddings
embeddings = generate_embeddings(chunks)

# Store them in notebook 1, document 1
stored = store_embeddings(
    embeddings=embeddings,
    notebook_id=1,
    document_id=1
)

print("Vectors stored:", stored)

# Search using the first chunk as the query
results = search_similar_chunks(
    query_embedding=embeddings[0]["embedding"],
    notebook_id=1,
    top_k=2
)

print("\nSearch results:")

for result in results:
    print(result)

print("\nTotal vectors:", get_vector_count(1))
