
from datetime import datetime, timezone
from app.extensions import db


class Notebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    documents = db.relationship(
        "Document",
        backref="notebook",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    notebook_id = db.Column(
        db.Integer,
        db.ForeignKey("notebook.id"),
        nullable=False
    )

    original_filename = db.Column(db.String(255), nullable=False)

    stored_filename = db.Column(db.String(255), nullable=False)

    file_path = db.Column(db.String(500), nullable=False)

    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    chunks = db.relationship(
        "Chunk",
        backref="document",
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    processing_status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )


class Chunk(db.Model):
    __tablename__ = "chunks"

    id = db.Column(db.Integer, primary_key=True)

    chunk_id = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("document.id"),
        nullable=False,
        index=True
    )

    notebook_id = db.Column(
        db.Integer,
        db.ForeignKey("notebook.id"),
        nullable=False,
        index=True
    )

    chunk_index = db.Column(db.Integer, nullable=False)

    page_number = db.Column(db.Integer, nullable=True)

    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_index"
        ),
    )
