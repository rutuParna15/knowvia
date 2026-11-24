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