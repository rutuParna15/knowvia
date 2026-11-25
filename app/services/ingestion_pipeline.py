
from app.services.document_processor import extract_document
from app.services.chunker import chunk_document
from app.services.chunk_repository import save_chunks


def ingest_document(document_id: int, file_path: str) -> dict:
    # Extract text
    pages = extract_document(file_path)

    # Generate chunks
    chunks = chunk_document(
        pages,
        chunk_size=1200,
        chunk_overlap=200
    )

    if not chunks:
        raise ValueError("No chunks generated from document.")

    # Save chunks in SQLite
    saved_count = save_chunks(document_id, chunks)

    return {
        "document_id": document_id,
        "total_pages": len(pages),
        "total_chunks": saved_count,
        "status": "completed"
    }
