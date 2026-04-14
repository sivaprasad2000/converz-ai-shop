from flask import Flask
from elasticsearch import Elasticsearch

from config import config
from app.extensions import db, migrate


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    app.elasticsearch = Elasticsearch(app.config["ELASTICSEARCH_URL"])

    from app.routes import register_blueprints
    register_blueprints(app)

    return app
