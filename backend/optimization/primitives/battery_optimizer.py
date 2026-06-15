from typing import Any, Dict, List, Optional


class BatteryOptimizer:
    def __init__(
        self,
        capacity_mwh: float,
        initial_soc_mwh: float,
        min_soc_mwh: float,
        max_charge_power_mw: float,
        max_discharge_power_mw: float,
        charge_efficiency: float = 0.95,
        discharge_efficiency: float = 0.95,
        trading_fee_eur_per_mwh: float = 0.0,
        market_access_fee_eur_per_mwh: float = 0.0,
        grid_fee_import_eur_per_mwh: float = 0.0,
        grid_fee_export_eur_per_mwh: float = 0.0,
        tax_or_levy_eur_per_mwh: float = 0.0,
        degradation_cost_eur_per_mwh_throughput: float = 0.0,
    ):
        self.capacity_mwh = capacity_mwh
        self.initial_soc_mwh = initial_soc_mwh
        self.min_soc_mwh = min_soc_mwh
        self.max_charge_power_mw = max_charge_power_mw
        self.max_discharge_power_mw = max_discharge_power_mw
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency

        self.trading_fee_eur_per_mwh = trading_fee_eur_per_mwh
        self.market_access_fee_eur_per_mwh = market_access_fee_eur_per_mwh
        self.grid_fee_import_eur_per_mwh = grid_fee_import_eur_per_mwh
        self.grid_fee_export_eur_per_mwh = grid_fee_export_eur_per_mwh
        self.tax_or_levy_eur_per_mwh = tax_or_levy_eur_per_mwh
        self.degradation_cost_eur_per_mwh_throughput = degradation_cost_eur_per_mwh_throughput

        self._validate_config()

    def _validate_config(self):
        if self.capacity_mwh <= 0:
            raise ValueError("capacity_mwh must be greater than 0")

        if self.min_soc_mwh < 0:
            raise ValueError("min_soc_mwh cannot be negative")

        if self.min_soc_mwh >= self.capacity_mwh:
            raise ValueError("min_soc_mwh must be lower than capacity_mwh")

        if not self.min_soc_mwh <= self.initial_soc_mwh <= self.capacity_mwh:
            raise ValueError("initial_soc_mwh must be between min_soc_mwh and capacity_mwh")

        if self.max_charge_power_mw <= 0:
            raise ValueError("max_charge_power_mw must be greater than 0")

        if self.max_discharge_power_mw <= 0:
            raise ValueError("max_discharge_power_mw must be greater than 0")

        if not 0 < self.charge_efficiency <= 1:
            raise ValueError("charge_efficiency must be between 0 and 1")

        if not 0 < self.discharge_efficiency <= 1:
            raise ValueError("discharge_efficiency must be between 0 and 1")

        cost_fields = [
            self.trading_fee_eur_per_mwh,
            self.market_access_fee_eur_per_mwh,
            self.grid_fee_import_eur_per_mwh,
            self.grid_fee_export_eur_per_mwh,
            self.tax_or_levy_eur_per_mwh,
            self.degradation_cost_eur_per_mwh_throughput,
        ]

        for cost in cost_fields:
            if cost < 0:
                raise ValueError("Commercial cost values cannot be negative")

    def _get_action_from_strategy(self, timestamp, strategy_hours):
        timestamp_text = str(timestamp)

        charge_timestamps = strategy_hours.get("charge_timestamps", [])
        discharge_timestamps = strategy_hours.get("discharge_timestamps", [])

        charge_hours = strategy_hours.get("charge_hours", [])
        discharge_hours = strategy_hours.get("discharge_hours", [])

        if timestamp_text in [str(value) for value in charge_timestamps]:
            return "charge"

        if timestamp_text in [str(value) for value in discharge_timestamps]:
            return "discharge"

        try:
            hour = int(str(timestamp_text)[11:13])
        except ValueError:
            return "idle"

        if hour in charge_hours:
            return "charge"

        if hour in discharge_hours:
            return "discharge"

        return "idle"

    def optimize(
        self,
        price_data: List[Dict[str, Any]],
        low_price_threshold: float,
        high_price_threshold: float,
        timestep_hours: float = 1.0,
        strategy_hours=None,
    ) -> List[Dict[str, Any]]:
        soc_mwh = self.initial_soc_mwh
        total_pnl_eur = 0.0
        results = []

        for row in price_data:
            timestamp = row["timestamp"]
            price = float(row["price"])

            action = "idle"
            grid_energy_mwh = 0.0
            battery_energy_mwh = 0.0
            market_value_eur = 0.0
            cost_eur = 0.0
            pnl_eur = 0.0

            if strategy_hours is not None:
                planned_action = self._get_action_from_strategy(timestamp, strategy_hours)
            else:
                planned_action = "idle"

                if price <= low_price_threshold:
                    planned_action = "charge"
                elif price >= high_price_threshold:
                    planned_action = "discharge"

            if planned_action == "charge":
                (
                    action,
                    grid_energy_mwh,
                    battery_energy_mwh,
                    market_value_eur,
                    cost_eur,
                    pnl_eur,
                    soc_mwh,
                ) = self._charge(
                    price=price,
                    soc_mwh=soc_mwh,
                    timestep_hours=timestep_hours,
                )

            elif planned_action == "discharge":
                (
                    action,
                    grid_energy_mwh,
                    battery_energy_mwh,
                    market_value_eur,
                    cost_eur,
                    pnl_eur,
                    soc_mwh,
                ) = self._discharge(
                    price=price,
                    soc_mwh=soc_mwh,
                    timestep_hours=timestep_hours,
                )

            total_pnl_eur += pnl_eur

            results.append(
                {
                    "timestamp": timestamp,
                    "price": price,
                    "action": action,
                    "soc_mwh": round(soc_mwh, 4),
                    "grid_energy_mwh": round(grid_energy_mwh, 4),
                    "battery_energy_mwh": round(battery_energy_mwh, 4),
                    "market_value_eur": round(market_value_eur, 2),
                    "cost_eur": round(cost_eur, 2),
                    "pnl_eur": round(pnl_eur, 2),
                    "total_pnl_eur": round(total_pnl_eur, 2),
                }
            )

        return results

    def _charge(self, price: float, soc_mwh: float, timestep_hours: float):
        available_storage_mwh = self.capacity_mwh - soc_mwh

        if available_storage_mwh <= 0:
            return "idle", 0.0, 0.0, 0.0, 0.0, 0.0, soc_mwh

        max_grid_energy_mwh = self.max_charge_power_mw * timestep_hours
        max_battery_energy_mwh = max_grid_energy_mwh * self.charge_efficiency

        battery_energy_mwh = min(
            available_storage_mwh,
            max_battery_energy_mwh,
        )

        grid_energy_mwh = battery_energy_mwh / self.charge_efficiency
        new_soc_mwh = min(soc_mwh + battery_energy_mwh, self.capacity_mwh)

        market_value_eur = -price * grid_energy_mwh

        variable_cost_per_mwh = (
            self.trading_fee_eur_per_mwh
            + self.market_access_fee_eur_per_mwh
            + self.grid_fee_import_eur_per_mwh
            + self.tax_or_levy_eur_per_mwh
        )

        cost_eur = (
            variable_cost_per_mwh * grid_energy_mwh
            + self.degradation_cost_eur_per_mwh_throughput * battery_energy_mwh
        )

        pnl_eur = market_value_eur - cost_eur

        return (
            "charge",
            grid_energy_mwh,
            battery_energy_mwh,
            market_value_eur,
            cost_eur,
            pnl_eur,
            new_soc_mwh,
        )

    def _discharge(self, price: float, soc_mwh: float, timestep_hours: float):
        available_battery_energy_mwh = soc_mwh - self.min_soc_mwh

        if available_battery_energy_mwh <= 0:
            return "idle", 0.0, 0.0, 0.0, 0.0, 0.0, soc_mwh

        max_battery_energy_mwh = self.max_discharge_power_mw * timestep_hours

        battery_energy_mwh = min(
            available_battery_energy_mwh,
            max_battery_energy_mwh,
        )

        grid_energy_mwh = battery_energy_mwh * self.discharge_efficiency
        new_soc_mwh = soc_mwh - battery_energy_mwh

        market_value_eur = price * grid_energy_mwh

        variable_cost_per_mwh = (
            self.trading_fee_eur_per_mwh
            + self.market_access_fee_eur_per_mwh
            + self.grid_fee_export_eur_per_mwh
        )

        cost_eur = (
            variable_cost_per_mwh * grid_energy_mwh
            + self.degradation_cost_eur_per_mwh_throughput * battery_energy_mwh
        )

        pnl_eur = market_value_eur - cost_eur

        return (
            "discharge",
            grid_energy_mwh,
            battery_energy_mwh,
            market_value_eur,
            cost_eur,
            pnl_eur,
            new_soc_mwh,
        )


