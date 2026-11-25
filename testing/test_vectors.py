from app.services.vector_store import get_vector_count

notebook_id = 2

count = get_vector_count(notebook_id)

print("Notebook ID:", notebook_id)
print("Stored vectors:", count)