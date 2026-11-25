
from sqlalchemy import select

from app.extensions import db
from app.models import Chunk, Document


def save_chunks(document_id: int, chunks: list[dict]) -> int:

    document = db.session.get(Document, document_id)

    if document is None:
        raise ValueError(f"Document {document_id} does not exist.")

    if not chunks:
        raise ValueError("Cannot save an empty chunk list.")

    records = []

    for chunk in chunks:
        content = chunk.get("text", "").strip()

        if not content:
            continue

        records.append(
            Chunk(
                chunk_id=chunk["chunk_id"],
                document_id=document_id,
                notebook_id=document.notebook_id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk.get("page_number"),
                content=content
            )
        )

    if not records:
        raise ValueError("No valid chunks found.")

    try:
        db.session.execute(
            db.delete(Chunk).where(
                Chunk.document_id == document_id
            )
        )

        db.session.add_all(records)
        db.session.commit()

        return len(records)

    except Exception:
        db.session.rollback()
        raise


def get_chunks_by_document(document_id: int):
    statement = (
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    )

    return db.session.scalars(statement).all()


def get_chunks_by_notebook(notebook_id: int):
    statement = (
        select(Chunk)
        .where(Chunk.notebook_id == notebook_id)
        .order_by(Chunk.document_id, Chunk.chunk_index)
    )

    return db.session.scalars(statement).all()


def delete_document_chunks(document_id: int) -> int:
    try:
        result = db.session.execute(
            db.delete(Chunk).where(
                Chunk.document_id == document_id
            )
        )

        db.session.commit()
        return result.rowcount

    except Exception:
        db.session.rollback()
        raise
