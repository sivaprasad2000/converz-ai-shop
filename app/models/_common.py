import enum
from datetime import datetime, timezone

from sqlalchemy import Integer, SmallInteger, VARCHAR
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.types import TypeDecorator

from app.extensions import db

# Cross-dialect unsigned integer types.
# MySQL gets the native unsigned type; SQLite falls back to a generic type.
UnsignedBigInt  = Integer()     .with_variant(BIGINT(unsigned=True),  "mysql")
UnsignedTinyInt = SmallInteger().with_variant(TINYINT(unsigned=True), "mysql")

_TABLE_OPTS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EnumType(TypeDecorator):
    """Stores an enum's string value in the DB; converts back to the enum on read."""

    impl = VARCHAR
    cache_ok = True

    def __init__(self, enum_class: type[enum.Enum], length: int = 50, **kw):
        self.enum_class = enum_class
        super().__init__(length, **kw)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum_class(value)
