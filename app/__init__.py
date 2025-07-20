from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SQLLITE_KEY')

    if not app.secret_key:
        raise ValueError("Please setup a SQL Lite key in your .env file")

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Import and register blueprint BEFORE importing models
    # This must occur here, we cannot put this import at the top
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # Setup app context
    with app.app_context():
        from . import models
        db.create_all()

    return app
