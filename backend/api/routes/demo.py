from fastapi import APIRouter

from backend.api.schemas import ApiResponse
from backend.services.investor_demo_seed import seed_investor_demo


router = APIRouter()


@router.post("/demo/investor-seed", response_model=ApiResponse)
def investor_demo_seed(
    asset_id: str | None = None,
    optimizer_engine: str = "rule_based_v1",
):
    try:
        return seed_investor_demo(
            asset_id=asset_id,
            optimizer_engine=optimizer_engine,
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not seed investor demo: {error}",
        }
