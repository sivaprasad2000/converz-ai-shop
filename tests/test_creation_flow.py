"""
Tests for the product creation flow:
  schema (ProductCreateQuery) → repository (ProductRepository) → service (ProductService)
"""
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.models.category import Category
from app.models.outbox import Outbox, OutboxStatus
from app.models.product import AvailabilityStatus, Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreateQuery
from app.services.product_service import ProductService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_query(**overrides) -> ProductCreateQuery:
    """Return a valid ProductCreateQuery; pass keyword args to override defaults."""
    defaults = dict(
        sku="TEST-SKU-001",
        title="Test Product",
        price=Decimal("9.99"),
        stock=10,
        min_order_quantity=1,
    )
    defaults.update(overrides)
    return ProductCreateQuery(**defaults)


# ---------------------------------------------------------------------------
# 1. Schema validation (pure unit — no DB needed)
# ---------------------------------------------------------------------------

class TestProductCreateQuery:
    def test_valid_query_succeeds(self):
        q = _minimal_query()
        assert q.sku == "TEST-SKU-001"
        assert q.price == Decimal("9.99")
        assert q.availability_status == AvailabilityStatus.IN_STOCK

    def test_price_zero_raises(self):
        with pytest.raises(ValueError, match="price must be greater than 0"):
            _minimal_query(price=Decimal("0"))

    def test_price_negative_raises(self):
        with pytest.raises(ValueError, match="price must be greater than 0"):
            _minimal_query(price=Decimal("-1.00"))

    def test_discount_over_100_raises(self):
        with pytest.raises(ValueError, match="discount_percentage must be between 0 and 100"):
            _minimal_query(discount_percentage=Decimal("100.01"))

    def test_discount_negative_raises(self):
        with pytest.raises(ValueError, match="discount_percentage must be between 0 and 100"):
            _minimal_query(discount_percentage=Decimal("-1"))

    def test_negative_stock_raises(self):
        with pytest.raises(ValueError, match="stock cannot be negative"):
            _minimal_query(stock=-1)

    def test_min_order_quantity_zero_raises(self):
        with pytest.raises(ValueError, match="min_order_quantity must be at least 1"):
            _minimal_query(min_order_quantity=0)

    def test_min_order_quantity_exceeds_stock_raises(self):
        with pytest.raises(ValueError, match="min_order_quantity cannot exceed stock"):
            _minimal_query(stock=5, min_order_quantity=6)

    def test_optional_fields_default_to_none(self):
        q = _minimal_query()
        assert q.description is None
        assert q.brand is None
        assert q.thumbnail is None
        assert q.category_id is None

    def test_full_query_with_all_fields(self):
        q = _minimal_query(
            description="A great product",
            brand="Acme",
            discount_percentage=Decimal("10.00"),
            weight=Decimal("1.50"),
            availability_status=AvailabilityStatus.LOW_STOCK,
            warranty_information="1 year",
            shipping_information="Ships in 2 days",
            return_policy="30-day returns",
            thumbnail="https://example.com/img.jpg",
            images=[{"url": "https://example.com/img.jpg", "sort_order": 0}],
            tags=["electronics", "gadget"],
            dimensions={"width": 10, "height": 5, "depth": 2},
            meta={"barcode": "123456"},
        )
        assert q.brand == "Acme"
        assert q.availability_status == AvailabilityStatus.LOW_STOCK


# ---------------------------------------------------------------------------
# 2. Repository layer (needs db_session)
# ---------------------------------------------------------------------------

class TestProductRepository:
    def test_create_persists_product(self, db_session):
        repo = ProductRepository()
        q = _minimal_query()
        product = repo.create(q)
        db_session.flush()

        assert product.id is not None
        assert product.sku == "TEST-SKU-001"
        assert product.title == "Test Product"
        assert product.price == Decimal("9.99")

    def test_create_sets_defaults(self, db_session):
        repo = ProductRepository()
        product = repo.create(_minimal_query())
        db_session.flush()

        assert product.availability_status == AvailabilityStatus.IN_STOCK
        assert product.discount_percentage == Decimal("0.00")
        assert product.stock == 10

    def test_create_with_category(self, db_session):
        category = Category(slug="electronics", name="Electronics")
        db_session.add(category)
        db_session.flush()

        repo = ProductRepository()
        product = repo.create(_minimal_query(category_id=category.id))
        db_session.flush()

        assert product.category_id == category.id

    def test_create_product_is_in_session(self, db_session):
        repo = ProductRepository()
        product = repo.create(_minimal_query(sku="UNIQUE-SKU"))
        db_session.flush()

        fetched = db_session.query(Product).filter_by(sku="UNIQUE-SKU").one()
        assert fetched.id == product.id

    def test_create_does_not_commit(self, db_session):
        """Repository must not commit — the caller owns the transaction boundary."""
        repo = ProductRepository()
        product = repo.create(_minimal_query(sku="NO-COMMIT-SKU"))
        # Product should be in session.new (pending insert, not yet flushed/committed)
        assert product in db_session.new


# ---------------------------------------------------------------------------
# 3. Service layer (needs db_session; commit is patched to flush-only)
# ---------------------------------------------------------------------------

@pytest.fixture()
def service_with_patched_commit(db_session):
    """
    ProductService calls db.session.commit(). Patch it to flush instead so the
    test transaction remains open and the db_session fixture can roll it back.
    """
    with patch("app.services.product_service.db.session.commit", side_effect=db_session.flush):
        yield ProductService()


class TestProductService:
    def test_create_product_returns_product(self, service_with_patched_commit):
        product = service_with_patched_commit.create_product(_minimal_query())
        assert isinstance(product, Product)
        assert product.id is not None

    def test_create_product_persists_correct_fields(self, db_session, service_with_patched_commit):
        product = service_with_patched_commit.create_product(
            _minimal_query(sku="SVC-SKU-001", title="Service Test", price=Decimal("19.99"))
        )
        fetched = db_session.query(Product).filter_by(sku="SVC-SKU-001").one()
        assert fetched.id == product.id
        assert fetched.title == "Service Test"
        assert fetched.price == Decimal("19.99")

    def test_create_product_writes_outbox_entry(self, db_session, service_with_patched_commit):
        product = service_with_patched_commit.create_product(_minimal_query(sku="OUTBOX-SKU"))
        outbox = db_session.query(Outbox).filter_by(aggregate_id=product.id).one()

        assert outbox.event_type == "product.created"
        assert outbox.status == OutboxStatus.PENDING

    def test_create_product_outbox_payload_matches_product(self, db_session, service_with_patched_commit):
        product = service_with_patched_commit.create_product(
            _minimal_query(sku="PAYLOAD-SKU", title="Payload Test", price=Decimal("5.00"))
        )
        outbox = db_session.query(Outbox).filter_by(aggregate_id=product.id).one()
        payload = outbox.payload

        assert payload["id"] == product.id
        assert payload["sku"] == "PAYLOAD-SKU"
        assert payload["title"] == "Payload Test"
        assert payload["price"] == 5.0
        assert payload["category"] is None  # no category assigned

    def test_create_product_outbox_payload_includes_category_slug(self, db_session, service_with_patched_commit):
        category = Category(slug="home-goods", name="Home Goods")
        db_session.add(category)
        db_session.flush()

        product = service_with_patched_commit.create_product(
            _minimal_query(sku="CAT-SKU", category_id=category.id)
        )
        outbox = db_session.query(Outbox).filter_by(aggregate_id=product.id).one()
        assert outbox.payload["category"] == "home-goods"
