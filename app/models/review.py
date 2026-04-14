from sqlalchemy import DateTime, Index, Text
from sqlalchemy.dialects.mysql import BIGINT, SMALLINT, VARCHAR
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models._common import _TABLE_OPTS, _utcnow


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_product_id", "product_id"),
        Index("ix_reviews_rating",     "rating"),
        _TABLE_OPTS,
    )

    id             = db.Column(BIGINT(unsigned=True),   primary_key=True, autoincrement=True)
    product_id     = db.Column(BIGINT(unsigned=True),   db.ForeignKey("products.id"), nullable=False)
    rating         = db.Column(SMALLINT(unsigned=True), nullable=False)  # 1–5
    comment        = db.Column(Text,                    nullable=True)
    reviewer_name  = db.Column(VARCHAR(300),            nullable=True)
    reviewer_email = db.Column(VARCHAR(500),            nullable=True)
    reviewed_at    = db.Column(DateTime, nullable=False, default=_utcnow)

    product = relationship("Product", back_populates="reviews")
