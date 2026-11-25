
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.prompt_service import build_qa_prompt
from app.services.llm_service import generate_response


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

    # 4. Prepare source references
    sources = []

    for chunk in retrieved_chunks:
        sources.append({
            "document_id": chunk.get("document_id"),
            "chunk_id": chunk.get("chunk_id"),
            "page_number": chunk.get("page_number"),
            "content": chunk.get("content")
        })

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }
