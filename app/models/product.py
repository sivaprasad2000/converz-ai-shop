import enum

from sqlalchemy import DateTime, Index, JSON, Numeric, Text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, VARCHAR
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models._common import _TABLE_OPTS, _utcnow, EnumType


class AvailabilityStatus(enum.Enum):
    IN_STOCK     = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK    = "low_stock"
    DISCONTINUED = "discontinued"


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_brand",               "brand"),
        Index("ix_products_price",               "price"),
        Index("ix_products_rating",              "rating"),
        Index("ix_products_availability_status", "availability_status"),
        Index("ix_products_stock",               "stock"),
        _TABLE_OPTS,
    )

    id                    = db.Column(BIGINT(unsigned=True),  primary_key=True, autoincrement=True)
    sku                   = db.Column(VARCHAR(100),           nullable=False, unique=True)
    title                 = db.Column(VARCHAR(500),           nullable=False)
    description           = db.Column(Text,                   nullable=True)
    brand                 = db.Column(VARCHAR(200),           nullable=True)
    price                 = db.Column(Numeric(12, 2),         nullable=False)
    discount_percentage   = db.Column(Numeric(5, 2),          nullable=False, default=0.00)
    rating                = db.Column(Numeric(3, 2),          nullable=False, default=0.00)
    review_count          = db.Column(INTEGER(unsigned=True), nullable=False, default=0)
    stock                 = db.Column(INTEGER(unsigned=True), nullable=False, default=0)
    min_order_quantity    = db.Column(INTEGER(unsigned=True), nullable=False, default=1)
    weight                = db.Column(Numeric(8, 2),          nullable=True)
    availability_status   = db.Column(EnumType(AvailabilityStatus, length=20), nullable=False, default=AvailabilityStatus.IN_STOCK)
    warranty_information  = db.Column(VARCHAR(500),           nullable=True)
    shipping_information  = db.Column(VARCHAR(500),           nullable=True)
    return_policy         = db.Column(VARCHAR(500),           nullable=True)
    thumbnail             = db.Column(VARCHAR(2048),          nullable=True)
    # [{"url": "...", "sort_order": 0}, ...]
    images                = db.Column(JSON,                   nullable=True)
    # ["mascara", "foundation", ...]
    tags                  = db.Column(JSON,                   nullable=True)
    # {"width": …, "height": …, "depth": …}
    dimensions            = db.Column(JSON,                   nullable=True)
    # {"barcode": …, "qr_code": …, "created_at": …, "updated_at": …}
    meta                  = db.Column(JSON,                   nullable=True)
    created_at            = db.Column(DateTime, nullable=False, default=_utcnow)
    updated_at            = db.Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    categories = relationship("Category", secondary="product_categories", back_populates="products")
    reviews    = relationship("Review",   back_populates="product", cascade="all, delete-orphan")
