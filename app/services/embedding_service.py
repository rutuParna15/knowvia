from functools import lru_cache

import torch
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

BATCH_SIZE = 32


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model once and reuse it.
    """

    model = SentenceTransformer(
        MODEL_NAME,
        device=DEVICE
    )

    model.eval()

    return model


def generate_embeddings(
    chunks: list[dict],
    batch_size: int = BATCH_SIZE
) -> list[dict]:
    """
    Generate embeddings for document chunks.

    Expected input:
    [
        {
            "chunk_id": "uuid",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Some document content..."
        }
    ]

    Returns:
    [
        {
            "chunk_id": "uuid",
            "chunk_index": 0,
            "page_number": 1,
            "embedding": [0.12, 0.34, ...]
        }
    ]
    """

    if not chunks:
        return []

    if batch_size < 1:
        raise ValueError("Batch size must be greater than zero.")

    valid_chunks = []

    for chunk in chunks:

        chunk_id = chunk.get("chunk_id")
        text = chunk.get("text", "").strip()

        if not chunk_id:
            raise ValueError("Every chunk must have a chunk_id.")

        if not text:
            continue

        valid_chunks.append({
            "chunk_id": chunk_id,
            "chunk_index": chunk.get("chunk_index"),
            "page_number": chunk.get("page_number"),
            "text": text
        })

    if not valid_chunks:
        return []

    model = get_embedding_model()

    texts = [chunk["text"] for chunk in valid_chunks]

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    results = []

    for chunk, embedding in zip(valid_chunks, embeddings):

        results.append({
            "chunk_id": chunk["chunk_id"],
            "chunk_index": chunk["chunk_index"],
            "page_number": chunk["page_number"],
            "embedding": embedding.tolist()
        })

    return results


def get_embedding_dimension() -> int:
    """
    Return the embedding vector dimension.
    """

    model = get_embedding_model()

    return model.get_sentence_embedding_dimension()
