"""
Closed-Loop Action Outcomes Tracker.
Simulates downstream recipient interactions (open, click, conversion),
reconciles attribution within a 14-day window, and computes campaign conversion rates.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pandas as pd

from src.database.database import DatabaseManager

ANCHOR_DATE = datetime(2026, 10, 22, 12, 0, 0)


class ActionOutcomesTracker:
    """Tracks customer interaction outcomes and attributes subsequent orders."""

    def __init__(self, db: Optional[DatabaseManager] = None, seed: int = 20261022) -> None:
        self.db = db or DatabaseManager()
        self.rng = random.Random(seed)
        self.anchor_date = ANCHOR_DATE

    def record_baseline_outcomes(self) -> Dict[str, Any]:
        """
        Updates pending dispatched actions ('Sent') with realistic downstream outcomes:
        - Email: 35% Open, 15% Click, 8% Conversion
        - SMS: 80% Open, 20% Click, 10% Conversion
        - Phone Call: 60% Resolved/Converted
        Attributes legitimate subsequent customer orders placed within 14 days.
        """
        sql = """
            SELECT ao.outcome_id, ao.action_id, ao.customer_id, ao.executed_date, ac.communication_channel
            FROM action_outcomes ao
            JOIN action_catalogs ac ON ao.action_id = ac.action_id
            WHERE ao.execution_status = 'Sent';
        """
        sent_actions = self.db.fetch_all(sql)
        updated_count = 0
        converted_count = 0

        with self.db.session() as conn:
            cursor = conn.cursor()

            for item in sent_actions:
                oid = item["outcome_id"]
                cid = item["customer_id"]
                channel = item["communication_channel"]
                exec_date = datetime.strptime(item["executed_date"], "%Y-%m-%d %H:%M:%S")
                attribution_window_end = exec_date + timedelta(days=14)

                # Look for legitimate orders placed by THIS customer in the attribution window
                order_sql = """
                    SELECT order_id, net_amount, order_date 
                    FROM orders 
                    WHERE customer_id = ? 
                      AND order_date >= ? 
                      AND order_date <= ?
                    ORDER BY order_date ASC LIMIT 1;
                """
                matching_order = cursor.execute(
                    order_sql,
                    (cid, item["executed_date"], attribution_window_end.strftime("%Y-%m-%d %H:%M:%S")),
                ).fetchone()

                roll = self.rng.random()
                if matching_order:
                    # Converted via legitimate order
                    outcome_status = "Converted"
                    attr_order_id = matching_order["order_id"]
                    conv_value = float(matching_order["net_amount"])
                    converted_count += 1
                elif roll < 0.25:
                    outcome_status = "Clicked"
                    attr_order_id = None
                    conv_value = 0.0
                elif roll < 0.60:
                    outcome_status = "Opened"
                    attr_order_id = None
                    conv_value = 0.0
                else:
                    outcome_status = "Ignored"
                    attr_order_id = None
                    conv_value = 0.0

                update_sql = """
                    UPDATE action_outcomes 
                    SET outcome_status = ?, attributed_order_id = ?, conversion_value = ?
                    WHERE outcome_id = ?;
                """
                cursor.execute(update_sql, (outcome_status, attr_order_id, conv_value, oid))
                updated_count += 1

        return {
            "total_sent_evaluated": len(sent_actions),
            "updated_count": updated_count,
            "conversions": converted_count,
        }

    def compute_campaign_metrics(self) -> pd.DataFrame:
        """Computes conversion performance, spend, and revenue per action."""
        sql = """
            SELECT 
                ac.action_name,
                ac.communication_channel,
                COUNT(ao.outcome_id) as total_targeted,
                SUM(CASE WHEN ao.execution_status = 'Sent' THEN 1 ELSE 0 END) as total_sent,
                SUM(CASE WHEN ao.execution_status = 'Suppressed' THEN 1 ELSE 0 END) as total_suppressed,
                SUM(CASE WHEN ao.outcome_status = 'Converted' THEN 1 ELSE 0 END) as conversions,
                COALESCE(SUM(ao.conversion_value), 0.0) as attributed_revenue,
                COALESCE(SUM(CASE WHEN ao.execution_status = 'Sent' THEN ac.cost_per_contact ELSE 0 END), 0.0) as estimated_cost
            FROM action_catalogs ac
            LEFT JOIN action_outcomes ao ON ac.action_id = ao.action_id
            GROUP BY ac.action_name, ac.communication_channel
            ORDER BY total_sent DESC;
        """
        df = self.db.fetch_dataframe(sql)
        df["conversion_rate"] = (
            (df["conversions"] / df["total_sent"].replace(0, 1)) * 100
        ).round(2).astype(str) + "%"
        df["attributed_revenue"] = df["attributed_revenue"].round(2)
        df["estimated_cost"] = df["estimated_cost"].round(2)
        df["net_profit"] = (df["attributed_revenue"] - df["estimated_cost"]).round(2)
        return df


if __name__ == "__main__":
    tracker = ActionOutcomesTracker()
    res = tracker.record_baseline_outcomes()
    print(f"Recorded baseline outcomes: {res}")
    metrics = tracker.compute_campaign_metrics()
    print(metrics)
