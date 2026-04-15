import click
from flask import current_app
from flask.cli import AppGroup

es_cli = AppGroup("es", help="Elasticsearch index management commands.")

PRODUCTS_INDEX = "products"

PRODUCTS_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "id":                   {"type": "long"},
            "sku":                  {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "english",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 500}
                },
            },
            "description":          {"type": "text", "analyzer": "english"},
            "brand":                {"type": "keyword"},
            "price":                {"type": "float"},
            "discount_percentage":  {"type": "float"},
            "rating":               {"type": "float"},
            "review_count":         {"type": "integer"},
            "stock":                {"type": "integer"},
            "min_order_quantity":   {"type": "integer"},
            "weight":               {"type": "float"},
            "availability_status":  {"type": "keyword"},
            "warranty_information": {"type": "text"},
            "shipping_information": {"type": "text"},
            "return_policy":        {"type": "text"},
            "thumbnail":            {"type": "keyword", "index": False},
            "tags":                 {"type": "keyword"},
            "images":               {"type": "object", "enabled": False},
            "dimensions": {
                "type": "object",
                "properties": {
                    "width":  {"type": "float"},
                    "height": {"type": "float"},
                    "depth":  {"type": "float"},
                },
            },
            "meta":       {"type": "object", "enabled": False},
        }
    },
}


@es_cli.command("create-index")
def create_index():
    """Create the products index with its mapping (no-op if it already exists)."""
    es = current_app.elasticsearch
    if es.indices.exists(index=PRODUCTS_INDEX):
        click.echo(f"Index '{PRODUCTS_INDEX}' already exists — skipping.")
        return
    es.indices.create(index=PRODUCTS_INDEX, body=PRODUCTS_MAPPING)
    click.echo(f"Index '{PRODUCTS_INDEX}' created.")


@es_cli.command("delete-index")
@click.confirmation_option(prompt=f"This will delete the '{PRODUCTS_INDEX}' index and all its data. Continue?")
def delete_index():
    """Delete the products index."""
    es = current_app.elasticsearch
    if not es.indices.exists(index=PRODUCTS_INDEX):
        click.echo(f"Index '{PRODUCTS_INDEX}' does not exist — skipping.")
        return
    es.indices.delete(index=PRODUCTS_INDEX)
    click.echo(f"Index '{PRODUCTS_INDEX}' deleted.")
