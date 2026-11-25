
import os
import uuid

from pathlib import Path

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app
)

from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Notebook, Document
from app.services.ingestion_pipeline import ingest_document


notebook_bp = Blueprint("notebooks", __name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@notebook_bp.route("/api/notebooks", methods=["POST"])
def create_notebook():

    # 1. Read form data
    notebook_name = request.form.get("name", "").strip()
    uploaded_files = request.files.getlist("files")

    if not notebook_name:
        return jsonify({
            "error": "Notebook name is required."
        }), 400

    if len(notebook_name) > 150:
        return jsonify({
            "error": "Notebook name cannot exceed 150 characters."
        }), 400

    if not uploaded_files or all(
        not file.filename for file in uploaded_files
    ):
        return jsonify({
            "error": "At least one document is required."
        }), 400

    # 2. Validate all files before creating the notebook
    for file in uploaded_files:

        if not file.filename:
            return jsonify({
                "error": "One of the uploaded files has no filename."
            }), 400

        extension = Path(file.filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            return jsonify({
                "error": f"Unsupported file format: {extension}"
            }), 400

    saved_file_paths = []

    try:
        # 3. Create notebook
        notebook = Notebook(name=notebook_name)

        db.session.add(notebook)
        db.session.commit()

        # 4. Create notebook-specific upload directory
        upload_root = Path(current_app.instance_path) / "uploads"

        notebook_folder = upload_root / str(notebook.id)
        notebook_folder.mkdir(parents=True, exist_ok=True)

        document_results = []

        # 5. Save and process each uploaded document
        for file in uploaded_files:

            original_filename = secure_filename(file.filename)

            extension = Path(original_filename).suffix.lower()

            stored_filename = f"{uuid.uuid4().hex}{extension}"

            file_path = notebook_folder / stored_filename

            # Save original document locally
            file.save(str(file_path))
            saved_file_paths.append(file_path)

            # Create document record
            document = Document(
                notebook_id=notebook.id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path)
            )

            db.session.add(document)
            db.session.commit()

            # 6. Automatically extract, chunk and persist
            try:
                result = ingest_document(
                    document_id=document.id,
                    file_path=str(file_path)
                )

                document_results.append({
                    **result,
                    "filename": original_filename
                })

            except Exception as e:
                current_app.logger.exception(
                    "Document ingestion failed: %s",
                    original_filename
                )

                document_results.append({
                    "document_id": document.id,
                    "filename": original_filename,
                    "status": "failed",
                    "error": str(e)
                })

        # 7. Return creation results
        return jsonify({
            "message": "Notebook created.",
            "notebook": {
                "id": notebook.id,
                "name": notebook.name
            },
            "documents": document_results
        }), 201

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Notebook creation failed."
        )

        # Remove files saved during a failed notebook creation
        for path in saved_file_paths:
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                current_app.logger.exception(
                    "Could not remove uploaded file: %s", path
                )

        return jsonify({
            "error": "Notebook creation failed."
        }), 500


@notebook_bp.route(
    "/api/notebooks/<int:notebook_id>/documents",
    methods=["POST"]
)
def add_documents(notebook_id):

    # 1. Check whether notebook exists
    notebook = db.session.get(Notebook, notebook_id)

    if notebook is None:
        return jsonify({
            "error": "Notebook not found."
        }), 404

    # 2. Get uploaded files
    uploaded_files = request.files.getlist("files")

    if not uploaded_files or all(
        not file.filename for file in uploaded_files
    ):
        return jsonify({
            "error": "At least one document is required."
        }), 400

    # 3. Validate files
    for file in uploaded_files:

        if not file.filename:
            return jsonify({
                "error": "One of the files has no filename."
            }), 400

        extension = Path(file.filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            return jsonify({
                "error": f"Unsupported file format: {extension}"
            }), 400

    # 4. Create notebook upload directory
    notebook_folder = (
        Path(current_app.instance_path)
        / "uploads"
        / str(notebook_id)
    )

    notebook_folder.mkdir(parents=True, exist_ok=True)

    saved_file_paths = []
    document_results = []

    try:

        # 5. Process each uploaded document
        for file in uploaded_files:

            original_filename = secure_filename(file.filename)

            extension = Path(original_filename).suffix.lower()

            stored_filename = f"{uuid.uuid4().hex}{extension}"

            file_path = notebook_folder / stored_filename

            # Save file locally
            file.save(str(file_path))
            saved_file_paths.append(file_path)

            # Create document record
            document = Document(
                notebook_id=notebook_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path)
            )

            db.session.add(document)
            db.session.commit()

            # 6. Automatically ingest document
            try:

                result = ingest_document(
                    document_id=document.id,
                    file_path=str(file_path)
                )

                document_results.append({
                    **result,
                    "filename": original_filename
                })

            except Exception as e:

                current_app.logger.exception(
                    "Document ingestion failed: %s",
                    original_filename
                )

                document_results.append({
                    "document_id": document.id,
                    "filename": original_filename,
                    "status": "failed",
                    "error": str(e)
                })

        return jsonify({
            "message": "Documents uploaded to notebook.",
            "notebook_id": notebook_id,
            "documents": document_results
        }), 201

    except Exception:

        db.session.rollback()

        current_app.logger.exception(
            "Document upload failed."
        )

        for path in saved_file_paths:
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                current_app.logger.exception(
                    "Could not remove file: %s", path
                )

        return jsonify({
            "error": "Document upload failed."
        }), 500


@notebook_bp.route("/api/notebooks", methods=["GET"])
def get_notebooks():
    notebooks = Notebook.query.order_by(
        Notebook.created_at.desc()
    ).all()

    return jsonify({
        "notebooks": [
            {
                "id": notebook.id,
                "name": notebook.name,
                "document_count": len(notebook.documents)
            }
            for notebook in notebooks
        ]
    }), 200
    
@notebook_bp.route(
    "/api/notebooks/<int:notebook_id>/documents",
    methods=["GET"]
)
def get_notebook_documents(notebook_id):

    # Check whether notebook exists
    notebook = db.session.get(Notebook, notebook_id)

    if notebook is None:
        return jsonify({
            "error": "Notebook not found."
        }), 404

    # Fetch documents belonging to this notebook
    documents = Document.query.filter_by(
        notebook_id=notebook_id
    ).order_by(Document.uploaded_at.desc()).all()

    return jsonify({
        "notebook_id": notebook.id,
        "notebook_name": notebook.name,
        "total_documents": len(documents),
        "documents": [
            {
                "id": document.id,
                "filename": document.original_filename,
                "uploaded_at": document.uploaded_at.isoformat(),
                "total_chunks": len(document.chunks)
            }
            for document in documents
        ]
    }), 200