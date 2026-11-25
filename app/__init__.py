
import os
from pathlib import Path

from flask import Flask
from app.extensions import db
from flask_migrate import Migrate

migrate = Migrate()

def create_app():

    app = Flask(__name__)

    # Create instance directory
    os.makedirs(app.instance_path, exist_ok=True)

    # Database configuration
    database_path = Path(app.instance_path) / "knowvia.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{database_path.as_posix()}"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Upload configuration
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.instance_path, "uploads"
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models before creating tables
    # with app.app_context():

    #     from app.models import Notebook, Document, Chunk

    #     db.create_all()

    # Register routes
    from app.routes.notebooks import notebook_bp
    app.register_blueprint(notebook_bp)
    
    from app.routes.pages import pages_bp
    app.register_blueprint(pages_bp)

    return app
