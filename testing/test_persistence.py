
from app import create_app
from app.extensions import db
from app.models import Notebook, Document, Chunk
from app.services.chunk_repository import (
    save_chunks,
    get_chunks_by_document,
    get_chunks_by_notebook
)

app = create_app()

with app.app_context():

    # --------------------------------
    # 1. Create test notebook
    # --------------------------------

    notebook = Notebook(name="Persistence Test")

    db.session.add(notebook)
    db.session.commit()

    print("Notebook created:", notebook.id)

    # --------------------------------
    # 2. Create test document
    # --------------------------------

    document = Document(
        notebook_id=notebook.id,
        original_filename="sample.pdf",
        stored_filename="test_sample.pdf",
        file_path="instance/uploads/test_sample.pdf"
    )

    db.session.add(document)
    db.session.commit()

    print("Document created:", document.id)

    # --------------------------------
    # 3. Create sample chunks
    # --------------------------------

    sample_chunks = [
        {
            "chunk_id": "test-chunk-001",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Machine learning is a subset of artificial intelligence."
        },
        {
            "chunk_id": "test-chunk-002",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Supervised learning uses labelled training data."
        },
        {
            "chunk_id": "test-chunk-003",
            "chunk_index": 2,
            "page_number": 2,
            "text": "Neural networks are inspired by biological neural systems."
        }
    ]

    # --------------------------------
    # 4. Save chunks
    # --------------------------------

    saved_count = save_chunks(
        document_id=document.id,
        chunks=sample_chunks
    )

    print("\nChunks saved:", saved_count)

    # --------------------------------
    # 5. Retrieve by document ID
    # --------------------------------

    print("\nRetrieving chunks by document ID:")

    document_chunks = get_chunks_by_document(document.id)

    for chunk in document_chunks:
        print("\nChunk ID:", chunk.chunk_id)
        print("Index:", chunk.chunk_index)
        print("Page:", chunk.page_number)
        print("Content:", chunk.content)

    # --------------------------------
    # 6. Retrieve by notebook ID
    # --------------------------------

    print("\nRetrieving chunks by notebook ID:")

    notebook_chunks = get_chunks_by_notebook(notebook.id)

    print("Total notebook chunks:", len(notebook_chunks))

    # --------------------------------
    # 7. Verify results
    # --------------------------------

    assert saved_count == 3
    assert len(document_chunks) == 3
    assert len(notebook_chunks) == 3

    assert document_chunks[0].chunk_index == 0
    assert document_chunks[0].page_number == 1

    print("\nAll persistence tests passed.")
