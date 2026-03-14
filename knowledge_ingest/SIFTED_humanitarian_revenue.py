import json
import os
from datetime import datetime
from typing import Dict, Any


ANALYTICS_FILE = os.path.join("analytics", "revenue_data.json")


def _load_analytics() -> Dict[str, Any]:
    """Load revenue analytics if available."""
    if not os.path.exists(ANALYTICS_FILE):
        return {}

    try:
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def estimate_revenue(cycle_index: int) -> float:
    """Estimate AI-generated revenue available for humanitarian aid.

    Priority:
    1. Use recent 30-day revenue from analytics if available.
    2. Otherwise fall back to a simple exponential growth model.
    """
    data = _load_analytics()
    daily = data.get("daily_revenue") or []
    if daily:
        # Use the most recent 30 days if we have them
        last_30 = daily[-30:] if len(daily) > 30 else daily
        avg_daily = sum(d.get("total", 0.0) for d in last_30) / max(
            1, len(last_30)
        )
        # Assume a small growth factor per humanitarian cycle
        growth_factor = 1.08 ** max(0, cycle_index)
        return round(avg_daily * 30 * growth_factor, 2)

    # Fallback: synthetic model similar to original humanitarian_orchestrator
    base = 1000.0
    growth = 1.20 ** max(0, cycle_index)
    return round(base * growth, 2)


if __name__ == "__main__":
    for i in range(3):
        print(f"Cycle {i+1}: estimated revenue = ${estimate_revenue(i):,.2f}")

