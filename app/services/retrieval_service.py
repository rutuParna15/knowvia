
import math
import re

from collections import Counter

from app.extensions import db
from app.models import Chunk

from app.services.embedding_service import generate_embeddings
from app.services.vector_store import search_similar_chunks


# BM25 parameters
BM25_K1 = 1.5
BM25_B = 0.75

# Reciprocal Rank Fusion parameter
RRF_K = 60


def tokenize(text: str) -> list[str]:
    """
    Convert text into lowercase tokens.
    Keeps numbers and alphanumeric technical terms.
    """
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())


def bm25_search(
    query: str,
    chunks: list[Chunk],
    top_k: int
) -> list[dict]:
    """
    Perform BM25 keyword retrieval over SQLite chunks.

    Returns ranked chunk IDs and BM25 scores.
    """

    query_terms = tokenize(query)

    if not query_terms or not chunks:
        return []

    # Tokenize each document chunk.
    tokenized_documents = [
        tokenize(chunk.content)
        for chunk in chunks
    ]

    document_frequencies = Counter()

    for tokens in tokenized_documents:
        document_frequencies.update(set(tokens))

    total_documents = len(chunks)

    average_document_length = (
        sum(len(tokens) for tokens in tokenized_documents)
        / total_documents
    )

    if average_document_length == 0:
        return []

    scores = []

    for chunk, tokens in zip(chunks, tokenized_documents):

        term_frequencies = Counter(tokens)
        document_length = len(tokens)

        score = 0.0

        for term in set(query_terms):

            frequency = term_frequencies.get(term, 0)

            if frequency == 0:
                continue

            document_frequency = document_frequencies[term]

            # BM25 inverse document frequency.
            idf = math.log(
                1 + (
                    total_documents - document_frequency + 0.5
                ) / (
                    document_frequency + 0.5
                )
            )

            # BM25 term frequency normalization.
            numerator = frequency * (BM25_K1 + 1)

            denominator = frequency + BM25_K1 * (
                1 - BM25_B
                + BM25_B * (
                    document_length / average_document_length
                )
            )

            score += idf * (numerator / denominator)

        if score > 0:
            scores.append({
                "chunk_id": chunk.chunk_id,
                "bm25_score": score
            })

    scores.sort(
        key=lambda item: item["bm25_score"],
        reverse=True
    )

    return scores[:top_k]


def reciprocal_rank_fusion(
    vector_results: list[dict],
    keyword_results: list[dict]
) -> list[dict]:
    """
    Combine vector and BM25 rankings using RRF.

    RRF score:
        1 / (k + vector_rank)
        +
        1 / (k + keyword_rank)
    """

    fused_results = {}

    # Process vector rankings.
    for rank, result in enumerate(vector_results, start=1):

        chunk_id = result["chunk_id"]

        fused_results[chunk_id] = {
            "chunk_id": chunk_id,
            "vector_rank": rank,
            "keyword_rank": None,
            "distance": result["distance"],
            "similarity": max(
                0.0,
                min(1.0, 1.0 - result["distance"])
            ),
            "bm25_score": None,
            "fusion_score": 1.0 / (RRF_K + rank)
        }

    # Process keyword rankings.
    for rank, result in enumerate(keyword_results, start=1):

        chunk_id = result["chunk_id"]

        if chunk_id not in fused_results:

            fused_results[chunk_id] = {
                "chunk_id": chunk_id,
                "vector_rank": None,
                "keyword_rank": rank,
                "distance": None,
                "similarity": None,
                "bm25_score": result["bm25_score"],
                "fusion_score": 0.0
            }

        else:

            fused_results[chunk_id]["keyword_rank"] = rank
            fused_results[chunk_id]["bm25_score"] = (
                result["bm25_score"]
            )

        fused_results[chunk_id]["fusion_score"] += (
            1.0 / (RRF_K + rank)
        )

    return sorted(
        fused_results.values(),
        key=lambda item: item["fusion_score"],
        reverse=True
    )


def retrieve_relevant_chunks(
    query: str,
    notebook_id: int,
    top_k: int = 5
) -> list[dict]:
    """
    Hybrid retrieval combining:
        1. ChromaDB semantic vector search.
        2. BM25 keyword search.
        3. Reciprocal Rank Fusion.
        4. SQLite chunk retrieval.

    All retrieval is restricted to the specified notebook.
    """

    query = query.strip()

    if not query:
        raise ValueError("Query cannot be empty.")

    if notebook_id < 1:
        raise ValueError("Invalid notebook ID.")

    if top_k < 1:
        raise ValueError("top_k must be greater than zero.")

    # Retrieve all chunks belonging to this notebook.
    notebook_chunks = (
        db.session.query(Chunk)
        .filter(Chunk.notebook_id == notebook_id)
        .all()
    )

    if not notebook_chunks:
        return []

    # Retrieve more candidates than the final requested count.
    candidate_k = max(top_k * 5, 20)

    # -----------------------------------------
    # 1. Semantic vector search
    # -----------------------------------------

    query_data = [{
        "chunk_id": "query",
        "chunk_index": 0,
        "page_number": None,
        "text": query
    }]

    query_embeddings = generate_embeddings(query_data)

    vector_results = []

    if query_embeddings:

        vector_results = search_similar_chunks(
            query_embedding=query_embeddings[0]["embedding"],
            notebook_id=notebook_id,
            top_k=candidate_k
        )

    # -----------------------------------------
    # 2. BM25 keyword search
    # -----------------------------------------

    keyword_results = bm25_search(
        query=query,
        chunks=notebook_chunks,
        top_k=candidate_k
    )

    # -----------------------------------------
    # 3. Combine rankings using RRF
    # -----------------------------------------

    fused_results = reciprocal_rank_fusion(
        vector_results=vector_results,
        keyword_results=keyword_results
    )

    # -----------------------------------------
    # 4. Retrieve original chunk content
    # -----------------------------------------

    chunks_by_id = {
        chunk.chunk_id: chunk
        for chunk in notebook_chunks
    }

    retrieved_chunks = []

    for result in fused_results[:top_k]:

        chunk = chunks_by_id.get(result["chunk_id"])

        if chunk is None:
            continue

        retrieved_chunks.append({
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "notebook_id": chunk.notebook_id,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "content": chunk.content,

            "distance": result["distance"],
            "similarity": result["similarity"],
            "bm25_score": result["bm25_score"],

            "vector_rank": result["vector_rank"],
            "keyword_rank": result["keyword_rank"],
            "fusion_score": result["fusion_score"]
        })

    return retrieved_chunks
