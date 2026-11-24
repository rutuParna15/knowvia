import os
from pathlib import Path

from flask import Flask
from app.extensions import db

def create_app():
    
    app = Flask(__name__)
    
    os.makedirs(app.instance_path, exist_ok=True)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{(Path(app.instance_path) / 'knowvia.db').as_posix()}"
    )
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.instance_path, "uploads"
    )
    
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
    
    db.init_app(app)
    
    from app.routes.notebooks import notebook_bp
    app.register_blueprint(notebook_bp)
    
    with app.app_context():
        from app.models import Notebook, Document
        db.create_all()

    return app