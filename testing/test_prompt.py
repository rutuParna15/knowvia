
from app.services.prompt_service import build_qa_prompt
from app.services.llm_service import generate_response

chunks = [
    {
        "content": (
            "Government transfer payments such as Social Security "
            "or unemployment insurance benefits are excluded from GDP "
            "because no current good or service is produced in exchange."
        ),
        "document_id": 7,
        "chunk_id": "test-chunk-001",
        "page_number": None
    }
]

question = "Why are transfer payments not counted as government purchases?"

prompt = build_qa_prompt(question, chunks)

answer = generate_response(prompt)

print("\nGenerated Answer:\n")
print(answer)
