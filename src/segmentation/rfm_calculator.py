"""
RFM Metrics Calculator.
Aggregates customer purchase history from SQLite to compute
Recency (days), Frequency (order count), and Monetary (net spend).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import pandas as pd

from src.database.database import DatabaseManager

# Fixed simulation anchor timestamp
ANCHOR_DATE = datetime(2026, 10, 22, 12, 0, 0)


class RFMCalculator:
    """Calculates customer-level RFM features from orders and returns."""

    def __init__(self, db: Optional[DatabaseManager] = None, anchor_date: datetime = ANCHOR_DATE) -> None:
        self.db = db or DatabaseManager()
        self.anchor_date = anchor_date

    def calculate_rfm(self) -> pd.DataFrame:
        """
        Executes an aggregation query joining customers and valid orders.
        Reconciles returns by summing orders.net_amount.
        """
        sql = """
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                c.email,
                c.created_at AS customer_registration_date,
                COUNT(o.order_id) AS frequency,
                COALESCE(SUM(o.net_amount), 0.0) AS monetary,
                MAX(o.order_date) AS most_recent_order_date
            FROM customers c
            LEFT JOIN orders o 
                ON c.customer_id = o.customer_id 
                AND o.order_status NOT IN ('Cancelled')
            GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.created_at
            ORDER BY c.customer_id;
        """
        df = self.db.fetch_dataframe(sql)

        # Convert date columns to datetime
        df["most_recent_order_date"] = pd.to_datetime(df["most_recent_order_date"])
        df["customer_registration_date"] = pd.to_datetime(df["customer_registration_date"])

        # Calculate Recency in full days relative to anchor date
        def calculate_recency(row: pd.Series) -> int:
            if pd.notnull(row["most_recent_order_date"]):
                delta = self.anchor_date - row["most_recent_order_date"]
                return max(0, delta.days)
            else:
                # For prospects with 0 purchases, recency is days since account creation
                delta = self.anchor_date - row["customer_registration_date"]
                return max(0, delta.days)

        df["recency_days"] = df.apply(calculate_recency, axis=1)
        df["monetary"] = df["monetary"].round(2)

        return df


if __name__ == "__main__":
    calc = RFMCalculator()
    rfm_df = calc.calculate_rfm()
    print(f"Computed RFM metrics for {len(rfm_df)} customers:")
    print(rfm_df[["customer_id", "frequency", "monetary", "recency_days"]].head())
