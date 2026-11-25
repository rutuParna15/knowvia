from app import create_app
from app.services.retrieval_service import retrieve_relevant_chunks

app = create_app()

with app.app_context():

    results = retrieve_relevant_chunks(
        query="Why are transfer payments not counted as government purchases?",
        notebook_id=2,
        top_k=5
    )

    for index, result in enumerate(results, start=1):

        print(f"\n{'=' * 60}")
        print(f"RESULT {index}")
        print(f"{'=' * 60}")

        print("Document:", result["document_id"])
        print("Page:", result["page_number"])

        print("Vector Rank:", result["vector_rank"])
        print("Keyword Rank:", result["keyword_rank"])

        print("Cosine Distance:", result["distance"])
        print("BM25 Score:", result["bm25_score"])
        print("Fusion Score:", result["fusion_score"])

        print("\nContent:")
        print(result["content"])