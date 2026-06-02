from fastapi import APIRouter

from src.assets.asset_loader import get_asset
from src.regulatory.germany_assumption_engine import (
    build_germany_requirements,
    build_germany_regulatory_assumptions,
)


router = APIRouter()


@router.get("/regulatory/germany/requirements")
def germany_regulatory_requirements():
    return {
        "status": "ok",
        "country": "Germany",
        "requirements": build_germany_requirements(),
    }


@router.get("/assets/{asset_id}/regulatory/germany")
def germany_asset_regulatory_assumptions(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    result = build_germany_regulatory_assumptions(asset).to_dict()

    return {
        "status": "ok",
        "asset_id": asset_id,
        "regulatory_assumptions": result,
    }
