from sqlalchemy import DateTime
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models._common import _TABLE_OPTS, _utcnow, UnsignedBigInt


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (_TABLE_OPTS,)

    id         = db.Column(UnsignedBigInt, primary_key=True, autoincrement=True)
    slug       = db.Column(VARCHAR(200), nullable=False, unique=True)
    name       = db.Column(VARCHAR(200), nullable=False)
    created_at = db.Column(DateTime, nullable=False, default=_utcnow)

    products = relationship("Product", back_populates="category")
