from typing import List, Optional

from pydantic import BaseModel


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
    timestep_hours: float = 1.0


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