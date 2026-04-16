from decimal import Decimal

from pydantic import BaseModel

from app.models.product import AvailabilityStatus


class ProductCreateQuery(BaseModel):
    sku: str
    title: str
    price: Decimal
    description: str | None = None
    brand: str | None = None
    discount_percentage: Decimal = Decimal("0.00")
    stock: int = 0
    min_order_quantity: int = 1
    weight: Decimal | None = None
    availability_status: AvailabilityStatus = AvailabilityStatus.IN_STOCK
    warranty_information: str | None = None
    shipping_information: str | None = None
    return_policy: str | None = None
    thumbnail: str | None = None
    images: list[dict] | None = None
    tags: list[str] | None = None
    dimensions: dict | None = None
    meta: dict | None = None
    category_id: int | None = None

    def model_post_init(self, __context: object) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be greater than 0")
        if not (Decimal("0") <= self.discount_percentage <= Decimal("100")):
            raise ValueError("discount_percentage must be between 0 and 100")
        if self.stock < 0:
            raise ValueError("stock cannot be negative")
        if self.min_order_quantity < 1:
            raise ValueError("min_order_quantity must be at least 1")
        if self.min_order_quantity > self.stock:
            raise ValueError("min_order_quantity cannot exceed stock")
