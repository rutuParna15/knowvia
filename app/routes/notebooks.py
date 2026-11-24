import os
import uuid

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Notebook, Document


notebook_bp = Blueprint("notebooks", __name__, url_prefix="/api")

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# 1. Create a notebook
@notebook_bp.route("/notebooks", methods=["POST"])
def create_notebook():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Notebook name is required"}), 400

    notebook = Notebook(name=name)

    db.session.add(notebook)
    db.session.commit()

    return jsonify({
        "message": "Notebook created successfully",
        "notebook": {
            "id": notebook.id,
            "name": notebook.name,
            "created_at": notebook.created_at.isoformat()
        }
    }), 201


# 2. Upload multiple documents to a notebook
@notebook_bp.route(
    "/notebooks/<int:notebook_id>/documents",
    methods=["POST"]
)
def upload_documents(notebook_id):

    notebook = db.session.get(Notebook, notebook_id)

    if not notebook:
        return jsonify({"error": "Notebook not found"}), 404

    files = request.files.getlist("documents")

    if not files or all(not f.filename for f in files):
        return jsonify({"error": "No documents provided"}), 400

    upload_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        str(notebook_id)
    )

    os.makedirs(upload_dir, exist_ok=True)

    uploaded_documents = []

    for file in files:

        if not file.filename:
            continue

        if not allowed_file(file.filename):
            continue

        original_filename = secure_filename(file.filename)

        extension = original_filename.rsplit(".", 1)[1].lower()

        stored_filename = f"{uuid.uuid4().hex}.{extension}"

        file_path = os.path.join(upload_dir, stored_filename)

        file.save(file_path)

        document = Document(
            notebook_id=notebook_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=os.path.relpath(
                file_path,
                current_app.instance_path
            )
        )

        db.session.add(document)

        uploaded_documents.append({
            "filename": original_filename,
            "stored_filename": stored_filename
        })

    if not uploaded_documents:
        return jsonify({
            "error": "No valid documents uploaded. Allowed: PDF, DOCX, TXT, MD"
        }), 400

    db.session.commit()

    return jsonify({
        "message": "Documents uploaded successfully",
        "notebook_id": notebook_id,
        "uploaded_documents": uploaded_documents
    }), 201


# 3. Get all notebooks
@notebook_bp.route("/notebooks", methods=["GET"])
def get_notebooks():

    notebooks = Notebook.query.order_by(
        Notebook.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": notebook.id,
            "name": notebook.name,
            "created_at": notebook.created_at.isoformat(),
            "document_count": len(notebook.documents)
        }
        for notebook in notebooks
    ])


# 4. Get all documents inside a notebook
@notebook_bp.route(
    "/notebooks/<int:notebook_id>/documents",
    methods=["GET"]
)
def get_documents(notebook_id):

    notebook = db.session.get(Notebook, notebook_id)

    if not notebook:
        return jsonify({"error": "Notebook not found"}), 404

    return jsonify([
        {
            "id": document.id,
            "filename": document.original_filename,
            "uploaded_at": document.uploaded_at.isoformat()
        }
        for document in notebook.documents
    ])