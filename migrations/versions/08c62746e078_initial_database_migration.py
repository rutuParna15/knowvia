
"""Initial database migration

Revision ID: 08c62746e078
Revises:
Create Date: 2026-11-25
"""

from alembic import op
import sqlalchemy as sa

revision = "08c62746e078"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create notebook table
    op.create_table(
        "notebook",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False
        )
    )

    # Create document table
    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "notebook_id",
            sa.Integer(),
            sa.ForeignKey("notebook.id"),
            nullable=False
        ),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False
        ),
        sa.Column(
            "stored_filename",
            sa.String(length=255),
            nullable=False
        ),
        sa.Column(
            "file_path",
            sa.String(length=500),
            nullable=False
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False
        ),
        sa.Column(
            "processing_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending"
        )
    )

    # Create chunks table
    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chunk_id",
            sa.String(length=36),
            nullable=False,
            unique=True
        ),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("document.id"),
            nullable=False
        ),
        sa.Column(
            "notebook_id",
            sa.Integer(),
            sa.ForeignKey("notebook.id"),
            nullable=False
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False
        ),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_index"
        )
    )

    # Create indexes
    op.create_index(
        "ix_chunks_chunk_id",
        "chunks",
        ["chunk_id"],
        unique=False
    )

    op.create_index(
        "ix_chunks_document_id",
        "chunks",
        ["document_id"],
        unique=False
    )

    op.create_index(
        "ix_chunks_notebook_id",
        "chunks",
        ["notebook_id"],
        unique=False
    )


def downgrade():
    op.drop_index("ix_chunks_notebook_id", table_name="chunks")
    op.drop_index("ix_chunks_document_id", table_name="chunks")
    op.drop_index("ix_chunks_chunk_id", table_name="chunks")

    op.drop_table("chunks")
    op.drop_table("document")
    op.drop_table("notebook")
