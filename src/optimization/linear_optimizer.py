import math

from src.config.commercial_config import DEFAULT_COMMERCIAL_CONFIG
from src.features.battery_usage_features import build_battery_usage_features
from src.optimization.base_optimizer import BaseDispatchOptimizer
from src.optimization.optimization_result import OptimizationResult
from src.signals.signal_engine import classify_opportunity


class LinearDispatchOptimizer(BaseDispatchOptimizer):
    optimizer_engine = "linear_v1"

    def optimize(
        self,
        price_data,
        battery_config,
        strategy_config,
        commercial_config=None,
    ):
        if commercial_config is None:
            commercial_config = DEFAULT_COMMERCIAL_CONFIG

        rows = self._clean_price_data(price_data)

        if not rows:
            return self._empty_result()

        timestep_hours = float(strategy_config.get("timestep_hours", 1.0))
        soc_states = self._build_soc_states(battery_config, strategy_config)
        initial_soc = self._snap_soc(
            float(battery_config["initial_soc_mwh"]),
            soc_states,
        )

        best_paths = {
            initial_soc: {
                "profit": 0.0,
                "steps": [],
            }
        }

        for row in rows:
            next_paths = {}

            for current_soc, path in best_paths.items():
                for next_soc in soc_states:
                    transition = self._build_transition(
                        row=row,
                        current_soc=current_soc,
                        next_soc=next_soc,
                        battery_config=battery_config,
                        commercial_config=commercial_config,
                        timestep_hours=timestep_hours,
                    )

                    if transition is None:
                        continue

                    candidate_profit = path["profit"] + transition["pnl_eur_raw"]

                    existing_path = next_paths.get(next_soc)

                    if (
                        existing_path is None
                        or candidate_profit > existing_path["profit"]
                    ):
                        next_paths[next_soc] = {
                            "profit": candidate_profit,
                            "steps": path["steps"] + [transition],
                        }

            best_paths = next_paths

        if not best_paths:
            return self._empty_result()

        terminal_soc = self._snap_soc(
            float(strategy_config.get("terminal_soc_mwh", initial_soc)),
            soc_states,
        )

        feasible_terminal_paths = [
            path for soc, path in best_paths.items()
            if soc >= terminal_soc
        ]

        if not feasible_terminal_paths:
            return self._empty_result()

        best_path = max(
            feasible_terminal_paths,
            key=lambda path: path["profit"],
        )

        dispatch_rows = self._finalize_dispatch(best_path["steps"])
        summary = self._build_summary(dispatch_rows, battery_config)

        return OptimizationResult(
            optimizer_engine=self.optimizer_engine,
            status="ok",
            summary=summary,
            dispatch=dispatch_rows,
            metadata={
                "method": "discrete_soc_dynamic_programming",
                "soc_state_count": len(soc_states),
                "soc_step_mwh": self._get_soc_step_mwh(
                    battery_config,
                    strategy_config,
                ),
                "objective_value_eur": round(best_path["profit"], 2),
                "constraint_status": "feasible",
                "terminal_soc_mwh": terminal_soc,
            },
        )

    def _clean_price_data(self, price_data):
        rows = []

        for row in price_data:
            try:
                rows.append(
                    {
                        "timestamp": row["timestamp"],
                        "price": float(row["price"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue

        return rows

    def _build_soc_states(self, battery_config, strategy_config):
        min_soc = float(battery_config["min_soc_mwh"])
        capacity = float(battery_config["capacity_mwh"])
        soc_step = self._get_soc_step_mwh(battery_config, strategy_config)

        state_count = int(math.floor((capacity - min_soc) / soc_step))
        states = [
            round(min_soc + index * soc_step, 6)
            for index in range(state_count + 1)
        ]

        if states[-1] < capacity:
            states.append(round(capacity, 6))

        return states

    def _get_soc_step_mwh(self, battery_config, strategy_config):
        configured_step = strategy_config.get("soc_step_mwh")

        if configured_step is not None:
            return max(float(configured_step), 0.01)

        capacity = float(battery_config["capacity_mwh"])

        return max(round(capacity / 40, 4), 0.1)

    def _snap_soc(self, soc_mwh, soc_states):
        return min(
            soc_states,
            key=lambda state: abs(state - soc_mwh),
        )

    def _build_transition(
        self,
        row,
        current_soc,
        next_soc,
        battery_config,
        commercial_config,
        timestep_hours,
    ):
        price = float(row["price"])
        delta_soc = round(next_soc - current_soc, 10)

        max_charge_energy = (
            float(battery_config["max_charge_power_mw"])
            * timestep_hours
            * float(battery_config["charge_efficiency"])
        )
        max_discharge_energy = (
            float(battery_config["max_discharge_power_mw"])
            * timestep_hours
        )

        if delta_soc > max_charge_energy + 1e-9:
            return None

        if -delta_soc > max_discharge_energy + 1e-9:
            return None

        action = "idle"
        grid_energy_mwh = 0.0
        battery_energy_mwh = 0.0
        market_value_eur = 0.0
        cost_eur = 0.0
        pnl_eur = 0.0

        if delta_soc > 1e-9:
            action = "charge"
            battery_energy_mwh = delta_soc
            grid_energy_mwh = delta_soc / float(battery_config["charge_efficiency"])
            market_value_eur = -price * grid_energy_mwh
            cost_eur = self._charge_cost(
                grid_energy_mwh,
                battery_energy_mwh,
                commercial_config,
            )
            pnl_eur = market_value_eur - cost_eur

        elif delta_soc < -1e-9:
            action = "discharge"
            battery_energy_mwh = abs(delta_soc)
            grid_energy_mwh = (
                battery_energy_mwh
                * float(battery_config["discharge_efficiency"])
            )
            market_value_eur = price * grid_energy_mwh
            cost_eur = self._discharge_cost(
                grid_energy_mwh,
                battery_energy_mwh,
                commercial_config,
            )
            pnl_eur = market_value_eur - cost_eur

        return {
            "timestamp": row["timestamp"],
            "price": price,
            "action": action,
            "soc_mwh": next_soc,
            "grid_energy_mwh": grid_energy_mwh,
            "battery_energy_mwh": battery_energy_mwh,
            "market_value_eur": market_value_eur,
            "cost_eur": cost_eur,
            "pnl_eur_raw": pnl_eur,
        }

    def _charge_cost(self, grid_energy_mwh, battery_energy_mwh, commercial_config):
        variable_cost_per_mwh = (
            float(commercial_config.get("trading_fee_eur_per_mwh", 0.0))
            + float(commercial_config.get("market_access_fee_eur_per_mwh", 0.0))
            + float(commercial_config.get("grid_fee_import_eur_per_mwh", 0.0))
            + float(commercial_config.get("tax_or_levy_eur_per_mwh", 0.0))
        )

        return (
            variable_cost_per_mwh * grid_energy_mwh
            + float(
                commercial_config.get(
                    "degradation_cost_eur_per_mwh_throughput",
                    0.0,
                )
            )
            * battery_energy_mwh
        )

    def _discharge_cost(self, grid_energy_mwh, battery_energy_mwh, commercial_config):
        variable_cost_per_mwh = (
            float(commercial_config.get("trading_fee_eur_per_mwh", 0.0))
            + float(commercial_config.get("market_access_fee_eur_per_mwh", 0.0))
            + float(commercial_config.get("grid_fee_export_eur_per_mwh", 0.0))
        )

        return (
            variable_cost_per_mwh * grid_energy_mwh
            + float(
                commercial_config.get(
                    "degradation_cost_eur_per_mwh_throughput",
                    0.0,
                )
            )
            * battery_energy_mwh
        )

    def _finalize_dispatch(self, steps):
        total_pnl_eur = 0.0
        dispatch_rows = []

        for step in steps:
            total_pnl_eur += step["pnl_eur_raw"]

            dispatch_rows.append(
                {
                    "timestamp": step["timestamp"],
                    "price": round(step["price"], 4),
                    "action": step["action"],
                    "soc_mwh": round(step["soc_mwh"], 4),
                    "grid_energy_mwh": round(step["grid_energy_mwh"], 4),
                    "battery_energy_mwh": round(step["battery_energy_mwh"], 4),
                    "market_value_eur": round(step["market_value_eur"], 2),
                    "cost_eur": round(step["cost_eur"], 2),
                    "pnl_eur": round(step["pnl_eur_raw"], 2),
                    "total_pnl_eur": round(total_pnl_eur, 2),
                }
            )

        return dispatch_rows

    def _build_summary(self, dispatch_rows, battery_config):
        if not dispatch_rows:
            return self._empty_summary()

        total_pnl_eur = dispatch_rows[-1]["total_pnl_eur"]
        battery_power_mw = float(battery_config["max_discharge_power_mw"])
        profit_per_mw_day = total_pnl_eur / battery_power_mw
        opportunity_level = classify_opportunity(profit_per_mw_day)

        charge_rows = [
            row for row in dispatch_rows
            if row["action"] == "charge"
        ]
        discharge_rows = [
            row for row in dispatch_rows
            if row["action"] == "discharge"
        ]

        usage_features = build_battery_usage_features(
            dispatch_rows=dispatch_rows,
            capacity_mwh=float(battery_config["capacity_mwh"]),
        )

        return {
            "signal": "ACTION" if total_pnl_eur > 0 else "NO_ACTION",
            "total_pnl_eur": round(total_pnl_eur, 2),
            "profit_per_mw_day": round(profit_per_mw_day, 2),
            "opportunity_level": opportunity_level,
            "charge_hours": len(charge_rows),
            "discharge_hours": len(discharge_rows),
            "first_charge_timestamp": charge_rows[0]["timestamp"] if charge_rows else None,
            "first_discharge_timestamp": discharge_rows[0]["timestamp"] if discharge_rows else None,
            "charged_mwh": usage_features["charged_mwh"],
            "discharged_mwh": usage_features["discharged_mwh"],
            "throughput_mwh": usage_features["throughput_mwh"],
            "equivalent_full_cycles": usage_features["equivalent_full_cycles"],
        }

    def _empty_summary(self):
        return {
            "signal": "NO_DATA",
            "total_pnl_eur": 0.0,
            "profit_per_mw_day": 0.0,
            "opportunity_level": "none",
            "charge_hours": 0,
            "discharge_hours": 0,
            "first_charge_timestamp": None,
            "first_discharge_timestamp": None,
            "charged_mwh": 0.0,
            "discharged_mwh": 0.0,
            "throughput_mwh": 0.0,
            "equivalent_full_cycles": 0.0,
        }

    def _empty_result(self):
        return OptimizationResult(
            optimizer_engine=self.optimizer_engine,
            status="no_data",
            summary=self._empty_summary(),
            dispatch=[],
            metadata={
                "method": "discrete_soc_dynamic_programming",
                "constraint_status": "no_data",
            },
        )
