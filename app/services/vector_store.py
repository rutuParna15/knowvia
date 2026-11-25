
import os
from pathlib import Path

import chromadb


# Project root: Knowvia/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Persistent local database location
VECTOR_DB_PATH = Path(
    os.getenv(
        "KNOWVIA_VECTOR_DB_PATH",
        str(PROJECT_ROOT / "instance" / "vector_db")
    )
)

COLLECTION_NAME = "knowvia_chunks"

_embedding_dimension = 384

_client = None
_collection = None


def get_collection():
    """
    Initialize and return the persistent ChromaDB collection.
    Reuses the same collection throughout the application lifecycle.
    """

    global _client, _collection

    if _collection is None:

        VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

        _client = chromadb.PersistentClient(
            path=str(VECTOR_DB_PATH)
        )

        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "description": "Knowvia document chunk embeddings",
                "hnsw:space": "cosine"
            }
        )

    return _collection


def store_embeddings(
    embeddings: list[dict],
    notebook_id: int,
    document_id: int
) -> int:
    """
    Store chunk embeddings in ChromaDB.

    Expected input:
    [
        {
            "chunk_id": "uuid",
            "chunk_index": 0,
            "page_number": 1,
            "embedding": [0.12, 0.34, ...]
        }
    ]

    Original chunk text remains in SQLite.
    """

    if not embeddings:
        return 0

    ids = []
    vectors = []
    metadatas = []

    for item in embeddings:

        chunk_id = item.get("chunk_id")
        embedding = item.get("embedding")

        if not chunk_id:
            raise ValueError("Missing chunk_id in embedding record.")

        if not embedding:
            raise ValueError(
                f"Missing embedding for chunk: {chunk_id}"
            )

        if len(embedding) != _embedding_dimension:
            raise ValueError(
                f"Expected {_embedding_dimension} dimensions, "
                f"received {len(embedding)} for chunk {chunk_id}."
            )

        metadata = {
            "notebook_id": int(notebook_id),
            "document_id": int(document_id),
            "chunk_index": int(item["chunk_index"])
        }

        if item.get("page_number") is not None:
            metadata["page_number"] = int(item["page_number"])

        ids.append(str(chunk_id))
        vectors.append(embedding)
        metadatas.append(metadata)

    collection = get_collection()

    collection.upsert(
        ids=ids,
        embeddings=vectors,
        metadatas=metadatas
    )

    return len(ids)


def replace_document_embeddings(
    embeddings: list[dict],
    notebook_id: int,
    document_id: int
) -> int:
    """
    Replace all embeddings belonging to a document.

    This also removes stale vectors when a document
    generates a different number of chunks after reprocessing.
    """

    collection = get_collection()

    collection.delete(
        where={
            "document_id": int(document_id)
        }
    )

    return store_embeddings(
        embeddings=embeddings,
        notebook_id=notebook_id,
        document_id=document_id
    )


def delete_document_embeddings(document_id: int) -> int:
    """
    Delete all vectors belonging to a document.
    """

    collection = get_collection()

    existing = collection.get(
        where={
            "document_id": int(document_id)
        },
        include=[]
    )

    ids = existing.get("ids", [])

    if ids:
        collection.delete(ids=ids)

    return len(ids)


def search_similar_chunks(
    query_embedding: list[float],
    notebook_id: int,
    top_k: int = 5
) -> list[dict]:
    """
    Retrieve the most semantically similar chunks
    from a particular notebook.

    Returns chunk IDs and metadata.
    Original text is retrieved separately from SQLite.
    """

    if not query_embedding:
        raise ValueError("Query embedding cannot be empty.")

    if len(query_embedding) != _embedding_dimension:
        raise ValueError(
            f"Expected {_embedding_dimension} dimensions, "
            f"received {len(query_embedding)}."
        )

    if top_k < 1:
        raise ValueError("top_k must be greater than zero.")

    collection = get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "notebook_id": int(notebook_id)
        },
        include=[
            "metadatas",
            "distances"
        ]
    )

    ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    matches = []

    for chunk_id, metadata, distance in zip(
        ids,
        metadatas,
        distances
    ):
        matches.append({
            "chunk_id": chunk_id,
            "metadata": metadata,
            "distance": float(distance)
        })

    return matches


def get_vector_count(
    notebook_id: int | None = None
) -> int:
    """
    Return total vector count or count for one notebook.
    """

    collection = get_collection()

    if notebook_id is None:
        return collection.count()

    results = collection.get(
        where={
            "notebook_id": int(notebook_id)
        },
        include=[]
    )

    return len(results["ids"])
