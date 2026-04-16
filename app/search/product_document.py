from app.models.product import Product


def build_product_document(product: Product) -> dict:
    return {
        "id":                   product.id,
        "sku":                  product.sku,
        "title":                product.title,
        "description":          product.description,
        "brand":                product.brand,
        "price":                float(product.price),
        "discount_percentage":  float(product.discount_percentage),
        "rating":               float(product.rating),
        "review_count":         product.review_count,
        "stock":                product.stock,
        "min_order_quantity":   product.min_order_quantity,
        "weight":               float(product.weight) if product.weight is not None else None,
        "availability_status":  product.availability_status.value if product.availability_status else None,
        "warranty_information": product.warranty_information,
        "shipping_information": product.shipping_information,
        "return_policy":        product.return_policy,
        "thumbnail":            product.thumbnail,
        "images":               product.images,
        "tags":                 product.tags,
        "dimensions":           product.dimensions,
        "meta":                 product.meta,
        "category":             product.category.slug if product.category else None,
    }
