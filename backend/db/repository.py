from __future__ import annotations

from dataclasses import dataclass

from backend.data_environment import normalize_data_mode
from backend.db.repositories import (
    execution_repository,
    revenue_repository,
    settlement_repository,
    signal_repository,
    telemetry_repository,
)


@dataclass(frozen=True)
class ModeRepository:
    data_mode: str

    def list_signals(self, asset_id: str, limit: int = 50):
        return signal_repository.list_signal_runs(
            asset_id=asset_id,
            limit=limit,
            data_mode=self.data_mode,
        )

    def list_revenue_stacks(self, asset_id: str, limit: int = 50):
        return revenue_repository.list_revenue_stack_runs(
            asset_id=asset_id,
            limit=limit,
            data_mode=self.data_mode,
        )

    def latest_settlement(self, asset_id: str):
        return settlement_repository.get_latest_settlement_reconciliation(
            asset_id=asset_id,
            data_mode=self.data_mode,
        )

    def list_settlements(self, asset_id: str, limit: int = 25):
        return settlement_repository.list_settlement_reconciliations(
            asset_id=asset_id,
            limit=limit,
            data_mode=self.data_mode,
        )

    def latest_telemetry(self, asset_id: str):
        return telemetry_repository.get_latest_telemetry_snapshot(
            asset_id=asset_id,
            data_mode=self.data_mode,
        )

    def list_telemetry(self, asset_id: str, limit: int = 25):
        return telemetry_repository.list_telemetry_snapshots(
            asset_id=asset_id,
            limit=limit,
            data_mode=self.data_mode,
        )

    def latest_execution_proposal(self, asset_id: str):
        return execution_repository.get_latest_execution_proposal(
            asset_id=asset_id,
            data_mode=self.data_mode,
        )

    def latest_paper_trade(self, asset_id: str):
        return execution_repository.get_latest_execution_paper_trade(
            asset_id=asset_id,
            data_mode=self.data_mode,
        )

    def latest_market_submission(self, asset_id: str):
        return execution_repository.get_latest_execution_market_submission(
            asset_id=asset_id,
            data_mode=self.data_mode,
        )

    def latest_approval(self, asset_id: str):
        return execution_repository.get_latest_execution_approval(
            asset_id=asset_id,
            data_mode=self.data_mode,
        )


def repository_for_mode(data_mode: str) -> ModeRepository:
    return ModeRepository(data_mode=normalize_data_mode(data_mode))
