from fastapi import APIRouter

from src.assets.asset_loader import get_asset
from src.markets.products.product_registry import (
    build_asset_product_eligibility_list,
    get_market_product,
    list_market_products,
)


router = APIRouter()


@router.get("/markets/products")
def market_products(country: str | None = None):
    products = list_market_products(country=country)

    return {
        "status": "ok",
        "product_count": len(products),
        "products": [
            product.to_dict()
            for product in products
        ],
    }


@router.get("/markets/products/{product_id}")
def market_product(product_id: str):
    try:
        product = get_market_product(product_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    return {
        "status": "ok",
        "product": product.to_dict(),
    }


@router.get("/assets/{asset_id}/eligible-products")
def asset_eligible_products(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    product_eligibility = build_asset_product_eligibility_list(asset)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "eligible_product_count": len(
            [
                result for result in product_eligibility
                if result["eligible"]
            ]
        ),
        "product_count": len(product_eligibility),
        "products": product_eligibility,
    }
