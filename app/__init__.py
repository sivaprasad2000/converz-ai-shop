from flask import Flask
from elasticsearch import Elasticsearch

from config import config
from app.extensions import db, migrate


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    es_url = app.config.get("ELASTICSEARCH_URL")
    app.elasticsearch = Elasticsearch(es_url) if es_url else None

    from app.routes import register_blueprints
    register_blueprints(app)

    from app.cli import es_cli
    app.cli.add_command(es_cli)

    return app
