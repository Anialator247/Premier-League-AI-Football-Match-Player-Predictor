from flask import Flask, jsonify
from flask_cors import CORS

from .extensions import db


def create_app(config=None):
    """Application factory. Tests pass their own config (e.g. in-memory DB)."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///childtracker.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if config:
        app.config.update(config)

    CORS(app)  # lets the frontend (different port) call the API
    db.init_app(app)

    from .routes.children import bp as children_bp
    from .routes.sleep import bp as sleep_bp
    from .routes.feeding import bp as feeding_bp

    app.register_blueprint(children_bp)
    app.register_blueprint(sleep_bp)
    app.register_blueprint(feeding_bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Not found"), 404

    with app.app_context():
        db.create_all()

    return app
