
from app.services.llm_service import generate_response

prompt = """
Explain why transfer payments are excluded from GDP.
Keep the answer concise.
"""

try:
    answer = generate_response(prompt)
    print("\nGenerated Answer:\n")
    print(answer)

except Exception as error:
    print(f"Error: {error}")
