from fastapi import APIRouter

from backend.ai_intelligence.priority_gaps import build_priority_gap_analysis
from backend.api.schemas import ApiResponse
from backend.data_environment import current_data_mode


router = APIRouter()


@router.get("/assets/{asset_id}/intelligence/priority-gaps", response_model=ApiResponse)
def asset_priority_gaps(asset_id: str, evidence_mode: str | None = None):
    return build_priority_gap_analysis(
        asset_id,
        evidence_mode=evidence_mode or current_data_mode(),
    )
