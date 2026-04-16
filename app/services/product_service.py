from app.extensions import db
from app.models.outbox import Outbox
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreateQuery
from app.search.product_document import build_product_document

_repo = ProductRepository()


class ProductService:
    def create_product(self, query: ProductCreateQuery) -> Product:
        """Create a product, link categories, queue an outbox event, and commit."""
        product = _repo.create(query)
        db.session.flush()  # ensure product.id is set before building the payload

        outbox_entry = Outbox(
            aggregate_id=product.id,
            event_type="product.created",
            payload=build_product_document(product),
        )
        db.session.add(outbox_entry)
        db.session.commit()
        return product
