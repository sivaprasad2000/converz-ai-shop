from flask import Blueprint, jsonify, current_app
from app.extensions import db

health_bp = Blueprint("health", __name__, url_prefix="/api/health")


@health_bp.get("/")
def health_check():
    status = {"status": "ok", "mysql": "ok", "elasticsearch": "ok"}
    http_status = 200

    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as exc:
        status["mysql"] = str(exc)
        status["status"] = "degraded"
        http_status = 503

    try:
        current_app.elasticsearch.ping()
    except Exception as exc:
        status["elasticsearch"] = str(exc)
        status["status"] = "degraded"
        http_status = 503

    return jsonify(status), http_status
