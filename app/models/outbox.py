import enum

from sqlalchemy import DateTime, Index, JSON
from sqlalchemy.dialects.mysql import BIGINT, TINYINT, VARCHAR

from app.extensions import db
from app.models._common import _TABLE_OPTS, _utcnow, EnumType


class OutboxStatus(enum.Enum):
    PENDING = "pending"
    SENT    = "sent"
    FAILED  = "failed"


class Outbox(db.Model):
    __tablename__ = "outbox"
    __table_args__ = (
        Index("ix_outbox_status_created_at", "status", "created_at"),
        _TABLE_OPTS,
    )

    id           = db.Column(BIGINT(unsigned=True),  primary_key=True, autoincrement=True)
    aggregate_id = db.Column(BIGINT(unsigned=True),  nullable=False)   # product_id
    event_type   = db.Column(VARCHAR(100),           nullable=False)   # e.g. "product.created"
    payload      = db.Column(JSON,                   nullable=False)   # full ES document
    status       = db.Column(EnumType(OutboxStatus, length=10), nullable=False, default=OutboxStatus.PENDING)
    attempts     = db.Column(TINYINT(unsigned=True), nullable=False, default=0)
    created_at   = db.Column(DateTime, nullable=False, default=_utcnow)
    processed_at = db.Column(DateTime, nullable=True)
