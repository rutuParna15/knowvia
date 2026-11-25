
from app import create_app
from app.services.qa_service import answer_question

app = create_app()

with app.app_context():
    result = answer_question(
        question="Why are transfer payments not counted as government purchases?",
        notebook_id=2,
        top_k=5
    )

    print("\nQUESTION:")
    print(result["question"])

    print("\nANSWER:")
    print(result["answer"])

    print("\nSOURCES:")

    for source in result["sources"]:
        print(source)
