from sqlalchemy import DateTime, Index
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models._common import _TABLE_OPTS, _utcnow


class ProductCategory(db.Model):
    __tablename__ = "product_categories"
    __table_args__ = (
        db.PrimaryKeyConstraint("product_id", "category_id"),
        Index("ix_product_categories_category_id", "category_id"),
        _TABLE_OPTS,
    )

    product_id  = db.Column(BIGINT(unsigned=True), db.ForeignKey("products.id"),   nullable=False)
    category_id = db.Column(BIGINT(unsigned=True), db.ForeignKey("categories.id"), nullable=False)


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (_TABLE_OPTS,)

    id         = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    slug       = db.Column(VARCHAR(200), nullable=False, unique=True)
    name       = db.Column(VARCHAR(200), nullable=False)
    created_at = db.Column(DateTime, nullable=False, default=_utcnow)

    products = relationship("Product", secondary="product_categories", back_populates="categories")
