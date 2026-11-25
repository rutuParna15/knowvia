
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.prompt_service import build_qa_prompt
from app.services.llm_service import generate_response


def has_insufficient_context(answer: str) -> bool:
    fallback = (
        "The provided documents do not contain enough "
        "information to answer this question."
    )

    return fallback.lower() in answer.lower()

def answer_question(
    question: str,
    notebook_id: int,
    top_k: int = 5
) -> dict:
    """
    Retrieve relevant chunks and generate a grounded answer.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not isinstance(notebook_id, int) or notebook_id < 1:
        raise ValueError("Invalid notebook ID.")

    # 1. Retrieve relevant document chunks
    retrieved_chunks = retrieve_relevant_chunks(
        query=question,
        notebook_id=notebook_id,
        top_k=top_k
    )

    # 2. Build prompt using retrieved context
    prompt = build_qa_prompt(
        question=question,
        retrieved_chunks=retrieved_chunks
    )

    # 3. Generate answer using local LLM
    answer = generate_response(prompt)

    # 4. If context is insufficient, do not return sources
    if has_insufficient_context(answer):
        sources = []
    else:
        sources = [
            {
                "document_id": chunk.get("document_id"),
                "chunk_id": chunk.get("chunk_id"),
                "page_number": chunk.get("page_number"),
                "content": chunk.get("content")
            }
            for chunk in retrieved_chunks
        ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }
