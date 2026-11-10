"""
Segment Rules Registry and Database Seeder.
Initializes the 7 standard explainable segment definitions into SegmentRule.
Uses ON CONFLICT DO UPDATE to prevent foreign-key deletion locks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from src.database.database import DatabaseManager

# Watertight, gap-free business thresholds
RULES_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "segment_id": "SEG-2026-000001",
        "segment_name": "Champions",
        "rfm_cell": "R5-F5-M5",
        "min_recency_days": 0,
        "max_recency_days": 30,
        "min_frequency": 5,
        "max_frequency": 999999,
        "min_monetary": 600.0,
        "max_monetary": 999999.0,
        "is_exclusive": 1,
        "priority_order": 1,
        "description": "High-value active buyers with frequent purchases and high net spend.",
    },
    {
        "segment_id": "SEG-2026-000002",
        "segment_name": "Loyal Customers",
        "rfm_cell": "R4-F4-M4",
        "min_recency_days": 0,
        "max_recency_days": 90,
        "min_frequency": 3,
        "max_frequency": 999999,
        "min_monetary": 250.0,
        "max_monetary": 999999.0,
        "is_exclusive": 1,
        "priority_order": 2,
        "description": "Consistent customers with regular purchases and solid lifetime value.",
    },
    {
        "segment_id": "SEG-2026-000003",
        "segment_name": "Potential Loyalists",
        "rfm_cell": "R4-F3-M3",
        "min_recency_days": 0,
        "max_recency_days": 90,
        "min_frequency": 2,
        "max_frequency": 999999,
        "min_monetary": 50.0,
        "max_monetary": 999999.0,
        "is_exclusive": 1,
        "priority_order": 3,
        "description": "Recent shoppers who have placed multiple orders and show repeat potential.",
    },
    {
        "segment_id": "SEG-2026-000004",
        "segment_name": "New Customers",
        "rfm_cell": "R5-F1-M1",
        "min_recency_days": 0,
        "max_recency_days": 90,
        "min_frequency": 1,
        "max_frequency": 1,
        "min_monetary": 0.0,
        "max_monetary": 999999.0,
        "is_exclusive": 1,
        "priority_order": 4,
        "description": "First-time customers who made their initial purchase in the last 90 days.",
    },
    {
        "segment_id": "SEG-2026-000005",
        "segment_name": "At Risk",
        "rfm_cell": "R2-F3-M4",
        "min_recency_days": 91,
        "max_recency_days": 180,
        "min_frequency": 1,
        "max_frequency": 999999,
        "min_monetary": 0.0,
        "max_monetary": 999999.0,
        "is_exclusive": 1,
        "priority_order": 5,
        "description": "Customers who have not purchased in 3 to 6 months.",
    },
    {
        "segment_id": "SEG-2026-000006",
        "segment_name": "Dormant Customers",
        "rfm_cell": "R1-F2-M2",
        "min_recency_days": 181,
        "max_recency_days": 999999,
        "min_frequency": 1,
        "max_frequency": 999999,
        "min_monetary": 0.0,
        "max_monetary": 999999.0,
        "is_exclusive": 1,
        "priority_order": 6,
        "description": "Inactive historical customers with no purchase activity for over 6 months.",
    },
    {
        "segment_id": "SEG-2026-000007",
        "segment_name": "Prospects",
        "rfm_cell": "R0-F0-M0",
        "min_recency_days": 0,
        "max_recency_days": 999999,
        "min_frequency": 0,
        "max_frequency": 0,
        "min_monetary": 0.0,
        "max_monetary": 0.0,
        "is_exclusive": 1,
        "priority_order": 7,
        "description": "Registered customer accounts that have not yet placed their first purchase.",
    },
]


def seed_segment_rules(db: DatabaseManager) -> None:
    """Inserts or updates default segment rules using UPSERT syntax."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
        INSERT INTO segment_rules (
            segment_id, segment_name, rfm_cell, min_recency_days, max_recency_days,
            min_frequency, max_frequency, min_monetary, max_monetary,
            is_exclusive, priority_order, description, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(segment_id) DO UPDATE SET
            segment_name = excluded.segment_name,
            rfm_cell = excluded.rfm_cell,
            min_recency_days = excluded.min_recency_days,
            max_recency_days = excluded.max_recency_days,
            min_frequency = excluded.min_frequency,
            max_frequency = excluded.max_frequency,
            min_monetary = excluded.min_monetary,
            max_monetary = excluded.max_monetary,
            is_exclusive = excluded.is_exclusive,
            priority_order = excluded.priority_order,
            description = excluded.description,
            is_active = excluded.is_active;
    """
    with db.session() as conn:
        cursor = conn.cursor()
        for rule in RULES_DEFINITIONS:
            cursor.execute(
                sql,
                (
                    rule["segment_id"],
                    rule["segment_name"],
                    rule["rfm_cell"],
                    rule["min_recency_days"],
                    rule["max_recency_days"],
                    rule["min_frequency"],
                    rule["max_frequency"],
                    rule["min_monetary"],
                    rule["max_monetary"],
                    rule["is_exclusive"],
                    rule["priority_order"],
                    rule["description"],
                    now_str,
                ),
            )


if __name__ == "__main__":
    db_mgr = DatabaseManager()
    seed_segment_rules(db_mgr)
    count = db_mgr.execute_scalar("SELECT COUNT(*) FROM segment_rules;")
    print(f"Successfully seeded {count} segment rules.")
