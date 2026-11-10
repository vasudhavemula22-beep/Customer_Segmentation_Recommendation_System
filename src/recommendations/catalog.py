"""
Action Catalog Definition and Seeder.
Populates action_catalogs with deterministic action IDs, communication channels,
cost metrics, and suppression periods. Auto-seeds segment_rules for FK safety.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from src.database.database import DatabaseManager
from src.segmentation.segment_rules import seed_segment_rules

CATALOG_ACTIONS: List[Dict[str, Any]] = [
    {
        "action_id": "ACTN-2026-000001",
        "action_name": "Customer Support Follow-up",
        "required_segment_id": None,
        "communication_channel": "Phone Call",
        "cost_per_contact": 4.50,
        "expected_conversion_rate": 0.85,
        "suppression_period_days": 3,
        "description": "Proactive service outreach by support agent to resolve active ticket.",
    },
    {
        "action_id": "ACTN-2026-000002",
        "action_name": "Premium Customer Benefit",
        "required_segment_id": "SEG-2026-000001",
        "communication_channel": "Email",
        "cost_per_contact": 0.15,
        "expected_conversion_rate": 0.28,
        "suppression_period_days": 14,
        "description": "Exclusive VIP tier appreciation perk and private collection access.",
    },
    {
        "action_id": "ACTN-2026-000003",
        "action_name": "Loyalty Reward",
        "required_segment_id": "SEG-2026-000002",
        "communication_channel": "Email",
        "cost_per_contact": 0.10,
        "expected_conversion_rate": 0.20,
        "suppression_period_days": 14,
        "description": "Double loyalty points offer and custom product cross-sell voucher.",
    },
    {
        "action_id": "ACTN-2026-000004",
        "action_name": "Discount Offer",
        "required_segment_id": "SEG-2026-000003",
        "communication_channel": "Email",
        "cost_per_contact": 0.08,
        "expected_conversion_rate": 0.15,
        "suppression_period_days": 14,
        "description": "Targeted 15% discount code to convert potential loyalty or prevent churn.",
    },
    {
        "action_id": "ACTN-2026-000005",
        "action_name": "Re-engagement Campaign",
        "required_segment_id": "SEG-2026-000006",
        "communication_channel": "SMS",
        "cost_per_contact": 0.05,
        "expected_conversion_rate": 0.08,
        "suppression_period_days": 30,
        "description": "Win-back text message with free shipping code and catalog highlights.",
    },
    {
        "action_id": "ACTN-2026-000006",
        "action_name": "Welcome Message",
        "required_segment_id": "SEG-2026-000004",
        "communication_channel": "Email",
        "cost_per_contact": 0.05,
        "expected_conversion_rate": 0.12,
        "suppression_period_days": 7,
        "description": "Onboarding orientation message, shopping guide, and customer service contacts.",
    },
]


def seed_action_catalog(db: DatabaseManager) -> None:
    """Seeds segment rules first, then catalog actions using UPSERT."""
    seed_segment_rules(db)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
        INSERT INTO action_catalogs (
            action_id, action_name, required_segment_id,
            communication_channel, cost_per_contact, expected_conversion_rate,
            suppression_period_days, is_active, description, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(action_id) DO UPDATE SET
            action_name = excluded.action_name,
            required_segment_id = excluded.required_segment_id,
            communication_channel = excluded.communication_channel,
            cost_per_contact = excluded.cost_per_contact,
            expected_conversion_rate = excluded.expected_conversion_rate,
            suppression_period_days = excluded.suppression_period_days,
            description = excluded.description;
    """
    with db.session() as conn:
        cursor = conn.cursor()
        for act in CATALOG_ACTIONS:
            cursor.execute(
                sql,
                (
                    act["action_id"],
                    act["action_name"],
                    act["required_segment_id"],
                    act["communication_channel"],
                    act["cost_per_contact"],
                    act["expected_conversion_rate"],
                    act["suppression_period_days"],
                    act["description"],
                    now_str,
                ),
            )


if __name__ == "__main__":
    db_mgr = DatabaseManager()
    seed_action_catalog(db_mgr)
    count = db_mgr.execute_scalar("SELECT COUNT(*) FROM action_catalogs;")
    print(f"Successfully seeded {count} catalog actions.")
