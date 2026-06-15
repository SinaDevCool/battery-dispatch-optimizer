from fastapi import APIRouter

from backend.ancillary.germany_ancillary_services import (
    assess_germany_ancillary_eligibility,
)
from backend.api.schemas import (
    AncillaryEligibilityResponse,
    ApiResponse,
    EegComplianceResponse,
    StorageClassificationResponse,
)
from backend.assets.asset_loader import get_asset
from backend.regulatory.eeg_compliance_checker import check_eeg_compliance
from backend.regulatory.germany_assumption_engine import (
    build_germany_requirements,
    build_germany_regulatory_assumptions,
)
from backend.regulatory.storage_classification import classify_storage_asset


router = APIRouter()


@router.get("/regulatory/germany/requirements", response_model=ApiResponse)
def germany_regulatory_requirements():
    return {
        "status": "ok",
        "country": "Germany",
        "requirements": build_germany_requirements(),
    }


@router.get("/assets/{asset_id}/regulatory/germany", response_model=ApiResponse)
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


@router.get(
    "/assets/{asset_id}/storage-classification",
    response_model=StorageClassificationResponse,
)
def asset_storage_classification(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    return classify_storage_asset(asset)


@router.get(
    "/assets/{asset_id}/eeg-compliance/latest",
    response_model=EegComplianceResponse,
)
def asset_eeg_compliance(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    return check_eeg_compliance(asset)


@router.get(
    "/assets/{asset_id}/ancillary/germany/eligibility",
    response_model=AncillaryEligibilityResponse,
)
def asset_germany_ancillary_eligibility(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    return assess_germany_ancillary_eligibility(asset)



