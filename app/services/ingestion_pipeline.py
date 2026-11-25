from sqlalchemy import update
from app.extensions import db
from app.models import Document

from app.services.document_processor import extract_document
from app.services.chunker import chunk_document
from app.services.chunk_repository import save_chunks
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import replace_document_embeddings


def update_status(document_id, status):
    result = db.session.execute(
        update(Document)
        .where(Document.id == document_id)
        .values(processing_status=status)
    )

    db.session.commit()

    print(
        f"Document {document_id}: "
        f"status updated to {status}, "
        f"rows affected: {result.rowcount}"
    )


def ingest_document(document_id: int, file_path: str) -> dict:

    document = db.session.get(Document, document_id)

    if document is None:
        raise ValueError(f"Document {document_id} does not exist.")

    notebook_id = document.notebook_id

    try:
        # Mark processing as started
        update_status(document_id, "processing")

        # Extract text
        pages = extract_document(file_path)

        if not pages:
            raise ValueError("No text extracted from document.")

        # Generate chunks
        chunks = chunk_document(
            pages,
            chunk_size=1200,
            chunk_overlap=200
        )

        if not chunks:
            raise ValueError("No chunks generated.")

        # Generate embeddings
        embeddings = generate_embeddings(chunks)

        if not embeddings:
            raise ValueError("No embeddings generated.")

        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count mismatch.")

        # Save chunks to SQLite
        saved_count = save_chunks(
            document_id=document_id,
            chunks=chunks
        )

        # Save embeddings to ChromaDB
        vector_count = replace_document_embeddings(
            embeddings=embeddings,
            notebook_id=notebook_id,
            document_id=document_id
        )

        # Mark processing as completed
        update_status(document_id, "completed")

        return {
            "document_id": document_id,
            "notebook_id": notebook_id,
            "total_pages": len(pages),
            "total_chunks": saved_count,
            "total_embeddings": vector_count,
            "status": "completed"
        }

    except Exception as e:
        db.session.rollback()

        document = db.session.get(Document, document_id)

        update_status(document_id, "failed")

        raise e
