from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ApiResponse(ApiBaseModel):
    status: str
    message: Optional[str] = None


class HealthResponse(ApiResponse):
    service: Optional[str] = None


class FileStatusResponse(ApiBaseModel):
    exists: bool
    path: str
    last_modified: Optional[str] = None
    size_bytes: int = 0


class DataStatusResponse(ApiResponse):
    forecast_file: Optional[FileStatusResponse] = None
    actual_price_file: Optional[FileStatusResponse] = None
    latest_signal_file: Optional[FileStatusResponse] = None
    scenario_file: Optional[FileStatusResponse] = None
    latest_monthly_report: Optional[FileStatusResponse] = None


class AssetResponse(ApiBaseModel):
    asset_id: str
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    country: Optional[str] = None
    market: Optional[str] = None
    capacity_mwh: Optional[float] = None
    max_charge_power_mw: Optional[float] = None
    max_discharge_power_mw: Optional[float] = None


class AssetListResponse(ApiResponse):
    asset_count: int = 0
    assets: List[AssetResponse] = Field(default_factory=list)


class SignalMetadataResponse(ApiBaseModel):
    source: Optional[str] = None
    forecast_provider: Optional[str] = None
    forecast_model: Optional[str] = None
    target_date: Optional[str] = None
    generated_at: Optional[str] = None
    forecast_file: Optional[str] = None


class AssetSignalDataResponse(ApiBaseModel):
    summary: Dict[str, Any] = Field(default_factory=dict)
    dispatch: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[SignalMetadataResponse] = None


class LatestSignalResponse(ApiResponse):
    asset_id: Optional[str] = None
    signal_file: Optional[str] = None
    data: Optional[AssetSignalDataResponse] = None


class AssetSignalRunResponse(ApiResponse):
    asset_id: Optional[str] = None
    optimizer_engine: Optional[str] = None
    asset_latest_signal_file: Optional[str] = None
    asset_run_file: Optional[str] = None
    signal_id: Optional[int] = None
    assumption_risk_flags: List[Dict[str, Any]] = Field(default_factory=list)
    validation: Optional[Dict[str, Any]] = None
    data: Optional[AssetSignalDataResponse] = None


class ForecastStatusResponse(ApiResponse):
    forecast_file: Optional[str] = None
    row_count: Optional[int] = None
    valid_row_count: Optional[int] = None
    negative_price_hours: Optional[int] = None
    duplicate_timestamps: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    average_price: Optional[float] = None
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    invalid_timestamps: Optional[int] = None
    missing_prices: Optional[int] = None


class ForecastPreviewResponse(ApiResponse):
    forecast_file: Optional[str] = None
    rows: Optional[int] = None
    columns: List[str] = Field(default_factory=list)
    market_profile_id: Optional[str] = None
    expected_intervals_per_day: Optional[int] = None
    market_time_unit_minutes: Optional[int] = None
    preview: List[Dict[str, Any]] = Field(default_factory=list)


class ForecastProfitabilityResponse(ApiResponse):
    comparison_file: Optional[str] = None
    forecast_sources: List[str] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)


class ActualPriceStatusResponse(ApiResponse):
    actual_file: Optional[FileStatusResponse] = None
    rows: Optional[int] = None
    valid_rows: Optional[int] = None
    columns: List[str] = Field(default_factory=list)
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    min_actual_price: Optional[float] = None
    max_actual_price: Optional[float] = None
    average_actual_price: Optional[float] = None
    invalid_timestamps: Optional[int] = None
    missing_prices: Optional[int] = None


class ForecastActualBacktestResponse(ApiResponse):
    asset_id: Optional[str] = None
    forecast_actual_id: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    run: Optional[Dict[str, Any]] = None


class RevenueStackResponse(ApiResponse):
    asset_id: Optional[str] = None
    optimizer_engine: Optional[str] = None
    total_estimated_revenue_eur: Optional[float] = None
    results: List[Dict[str, Any]] = Field(default_factory=list)


class RevenueAllocationResponse(ApiResponse):
    asset_id: Optional[str] = None
    optimizer_engine: Optional[str] = None
    allocation: Optional[Any] = None
    results: List[Dict[str, Any]] = Field(default_factory=list)


class StorageClassificationResponse(ApiResponse):
    asset_id: Optional[str] = None
    storage_classification: Optional[str] = None
    market_participation_mode: Optional[str] = None


class EegComplianceResponse(ApiResponse):
    asset_id: Optional[str] = None
    eeg_eligible: Optional[bool] = None
    green_colocation: Optional[bool] = None
    mixed_origin_risk: Optional[str] = None
    compliance_notes: List[str] = Field(default_factory=list)


class AncillaryEligibilityResponse(ApiResponse):
    asset_id: Optional[str] = None
    eligible: Optional[bool] = None
    eligible_products: List[str] = Field(default_factory=list)
    reason: Optional[str] = None


class GridFeeSensitivityResponse(ApiResponse):
    asset_id: Optional[str] = None
    signal_status: Optional[str] = None
    sensitivity: List[Dict[str, Any]] = Field(default_factory=list)


class HedgingRevenueResponse(ApiResponse):
    asset_id: Optional[str] = None
    merchant_revenue_eur: Optional[float] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
    contracts: List[Dict[str, Any]] = Field(default_factory=list)


class MonthlyReportResponse(ApiResponse):
    report_name: Optional[str] = None
    report_title: Optional[str] = None
    report_period: Optional[str] = None


class PricePoint(BaseModel):
    timestamp: str
    price: float


class BatteryConfigRequest(BaseModel):
    capacity_mwh: float = 20.0
    initial_soc_mwh: float = 10.0
    min_soc_mwh: float = 2.0
    max_charge_power_mw: float = 10.0
    max_discharge_power_mw: float = 10.0
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95


class StrategyConfigRequest(BaseModel):
    low_price_threshold: float = 20.0
    high_price_threshold: float = 80.0
    timestep_hours: float = 0.25


class BatterySignalRequest(BaseModel):
    price_data: List[PricePoint]
    battery_config: Optional[BatteryConfigRequest] = None
    strategy_config: Optional[StrategyConfigRequest] = None


class DispatchRow(BaseModel):
    timestamp: str
    price: float
    action: str
    soc_mwh: float
    grid_energy_mwh: float
    battery_energy_mwh: float
    pnl_eur: float
    total_pnl_eur: float


class BatterySignalSummary(BaseModel):
    signal: str
    total_pnl_eur: float
    profit_per_mw_day: float
    opportunity_level: str
    charge_hours: int
    discharge_hours: int
    first_charge_timestamp: Optional[str] = None
    first_discharge_timestamp: Optional[str] = None


class BatterySignalResponse(BaseModel):
    summary: BatterySignalSummary
    dispatch: List[DispatchRow]


class BacktestRequest(BaseModel):
    price_data: List[PricePoint]
    battery_config: Optional[BatteryConfigRequest] = None
    strategy_config: Optional[StrategyConfigRequest] = None


class BacktestSummary(BaseModel):
    total_pnl_eur: float
    hours: int
    charge_hours: int
    discharge_hours: int
    idle_hours: int
    min_soc_mwh: Optional[float] = None
    max_soc_mwh: Optional[float] = None
    average_pnl_per_hour_eur: float


class BacktestResponse(BaseModel):
    summary: BacktestSummary
    dispatch: List[DispatchRow]

class BatteryConfigResponse(BaseModel):
    battery_config: BatteryConfigRequest
    strategy_config: StrategyConfigRequest



