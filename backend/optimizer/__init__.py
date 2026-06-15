"""Compatibility imports for the old optimizer package.

New code should import primitive optimizer helpers from
``backend.optimization.primitives``. This package remains so older callers do not
break immediately.
"""

from backend.optimization.primitives import BatteryOptimizer, find_daily_arbitrage_hours
from backend.optimization.primitives.dispatch_strategy import (
    get_action_for_timestamp,
    get_aggressive_strategy,
    get_conservative_strategy,
    get_simple_threshold_strategy,
)

__all__ = [
    "BatteryOptimizer",
    "find_daily_arbitrage_hours",
    "get_action_for_timestamp",
    "get_aggressive_strategy",
    "get_conservative_strategy",
    "get_simple_threshold_strategy",
]



