
from app.services.document_processor import extract_document

file_path = "test.txt"

pages = extract_document(file_path)

for page in pages:
    print(f"\n--- Page {page['page_number']} ---")
    print(page["text"])

print(f"\nTotal pages extracted: {len(pages)}")
