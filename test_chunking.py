
from app.services.document_processor import extract_document
from app.services.chunker import chunk_document

file_path = "test.txt"

# Step 1: Extract text
pages = extract_document(file_path)

# Step 2: Generate chunks
chunks = chunk_document(
    pages,
    chunk_size=1200,
    chunk_overlap=200
)

# Step 3: Display results
for chunk in chunks:
    print(f"\nChunk ID: {chunk['chunk_id']}")
    print(f"Chunk Index: {chunk['chunk_index']}")
    print(f"Page Number: {chunk['page_number']}")
    print(f"Characters: {len(chunk['text'])}")
    print("-" * 50)
    print(chunk["text"])

print(f"\nTotal chunks generated: {len(chunks)}")
