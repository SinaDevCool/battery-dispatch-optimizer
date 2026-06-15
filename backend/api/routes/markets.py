from fastapi import APIRouter

from backend.markets.market_profile_loader import (
    get_market_profile,
    load_market_profiles,
)


router = APIRouter()


@router.get("/markets")
def list_markets():
    profiles = load_market_profiles()

    return {
        "status": "ok",
        "market_count": len(profiles),
        "markets": profiles,
    }


@router.get("/markets/{market_profile_id}")
def market_profile(market_profile_id: str):
    try:
        profile = get_market_profile(market_profile_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    return {
        "status": "ok",
        "market": profile,
    }



