from app.extensions import db
from app.models.product import Product
from app.schemas.product import ProductCreateQuery


class ProductRepository:
    def create(self, query: ProductCreateQuery) -> Product:
        """Persist a new product. Does NOT commit — the caller controls the transaction boundary."""
        product = Product(
            sku=query.sku,
            title=query.title,
            description=query.description,
            brand=query.brand,
            price=query.price,
            discount_percentage=query.discount_percentage,
            stock=query.stock,
            min_order_quantity=query.min_order_quantity,
            weight=query.weight,
            availability_status=query.availability_status,
            warranty_information=query.warranty_information,
            shipping_information=query.shipping_information,
            return_policy=query.return_policy,
            thumbnail=query.thumbnail,
            images=query.images,
            tags=query.tags,
            dimensions=query.dimensions,
            meta=query.meta,
            category_id=query.category_id,
        )
        db.session.add(product)
        return product
