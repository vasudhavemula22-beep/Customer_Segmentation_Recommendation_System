"""
Explainable Segmentation Engine.
Evaluates RFM features against prioritized rules, formats human-readable
assignment explanations, and records SCD Type 2 memberships in SQLite.
Uses UPSERT to guarantee idempotent history management without primary key clashes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.database.database import DatabaseManager
from src.segmentation.rfm_calculator import RFMCalculator
from src.segmentation.segment_rules import RULES_DEFINITIONS, seed_segment_rules


class SegmentationEngine:
    """Evaluates and persists explainable customer segment memberships."""

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or DatabaseManager()
        self.calculator = RFMCalculator(db=self.db)

    def _fetch_active_rules(self) -> List[Dict[str, Any]]:
        """Loads all active rules ordered by evaluation priority."""
        sql = """
            SELECT * FROM segment_rules 
            WHERE is_active = 1 
            ORDER BY priority_order ASC;
        """
        rows = self.db.fetch_all(sql)
        return [dict(r) for r in rows]

    def _generate_explanation(self, row: pd.Series, rule: Dict[str, Any]) -> str:
        """Constructs an explainable natural-language justification for the segment assignment."""
        r = int(row["recency_days"])
        f = int(row["frequency"])
        m = float(row["monetary"])
        name = rule["segment_name"]

        if name == "Champions":
            return f"Purchased {r} days ago (<= 30d), ordered {f} times (>= 5), spent ${m:.2f} (>= $600.00)."
        elif name == "Loyal Customers":
            return f"Purchased {r} days ago (<= 90d), ordered {f} times (>= 3), spent ${m:.2f} (>= $250.00)."
        elif name == "Potential Loyalists":
            return f"Purchased {r} days ago (<= 90d), placed {f} orders (>= 2), spent ${m:.2f} (>= $50.00)."
        elif name == "New Customers":
            return f"First-time buyer with 1 order, purchased {r} days ago (<= 90d), spent ${m:.2f}."
        elif name == "At Risk":
            return f"Purchased {r} days ago (91-180d), placed {f} orders, spent ${m:.2f}."
        elif name == "Dormant Customers":
            return f"Inactive for {r} days (> 180d) with {f} historical orders, total spend ${m:.2f}."
        elif name == "Prospects":
            return f"Registered account with 0 purchases to date ($0.00 spent)."
        else:
            return f"Assigned to {name} based on Recency: {r}d, Frequency: {f}, Monetary: ${m:.2f}."

    def assign_segments(self, rfm_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Iterates through customers and finds the first matching exclusive rule by priority."""
        rules = self._fetch_active_rules()
        memberships: List[Dict[str, Any]] = []

        for _, row in rfm_df.iterrows():
            cid = row["customer_id"]
            r = row["recency_days"]
            f = row["frequency"]
            m = row["monetary"]

            assigned_rule = None
            for rule in rules:
                matches_r = (rule["min_recency_days"] is None or r >= rule["min_recency_days"]) and \
                            (rule["max_recency_days"] is None or r <= rule["max_recency_days"])
                matches_f = (rule["min_frequency"] is None or f >= rule["min_frequency"]) and \
                            (rule["max_frequency"] is None or f <= rule["max_frequency"])
                matches_m = (rule["min_monetary"] is None or m >= rule["min_monetary"]) and \
                            (rule["max_monetary"] is None or m <= rule["max_monetary"])

                if matches_r and matches_f and matches_m:
                    assigned_rule = rule
                    break

            if assigned_rule is None:
                assigned_rule = rules[-1]

            reason = self._generate_explanation(row, assigned_rule)
            membership_id = f"MEM-{assigned_rule['segment_id']}-{cid}"

            memberships.append({
                "membership_id": membership_id,
                "segment_id": assigned_rule["segment_id"],
                "segment_name": assigned_rule["segment_name"],
                "customer_id": cid,
                "confidence_score": 1.0,
                "assignment_reason": reason,
                "recency_days": r,
                "frequency": f,
                "monetary": m,
            })

        return memberships

    def persist_memberships_scd2(self, memberships: List[Dict[str, Any]], effective_date: Optional[str] = None) -> Tuple[int, int]:
        """
        Persists memberships with Slowly Changing Dimension Type 2 semantics:
        - If active membership matches, it is preserved.
        - If segment changed, previous active record is expired (valid_to set) and new record inserted/reactivated.
        """
        now_str = effective_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        active_sql = "SELECT customer_id, segment_id, membership_id FROM segment_memberships WHERE is_active = 1;"
        active_records = {r["customer_id"]: dict(r) for r in self.db.fetch_all(active_sql)}

        inserted_count = 0
        updated_count = 0

        with self.db.session() as conn:
            cursor = conn.cursor()

            for mem in memberships:
                cid = mem["customer_id"]
                new_seg_id = mem["segment_id"]
                mem_id = mem["membership_id"]
                reason = mem["assignment_reason"]

                if cid in active_records:
                    current_active = active_records[cid]
                    if current_active["segment_id"] == new_seg_id:
                        continue

                    # Expire previous active membership
                    expire_sql = """
                        UPDATE segment_memberships 
                        SET is_active = 0, valid_to = ? 
                        WHERE customer_id = ? AND is_active = 1;
                    """
                    cursor.execute(expire_sql, (now_str, cid))
                    updated_count += 1

                # Insert new active membership or reactivate using UPSERT
                insert_sql = """
                    INSERT INTO segment_memberships (
                        membership_id, segment_id, customer_id,
                        assigned_date, valid_from, valid_to,
                        is_active, confidence_score, assignment_reason
                    ) VALUES (?, ?, ?, ?, ?, NULL, 1, 1.0, ?)
                    ON CONFLICT(membership_id) DO UPDATE SET
                        assigned_date = excluded.assigned_date,
                        valid_from = excluded.valid_from,
                        valid_to = NULL,
                        is_active = 1,
                        confidence_score = excluded.confidence_score,
                        assignment_reason = excluded.assignment_reason;
                """
                cursor.execute(
                    insert_sql,
                    (mem_id, new_seg_id, cid, now_str, now_str, reason),
                )
                inserted_count += 1

        return inserted_count, updated_count

    def execute_segmentation_run(self) -> Dict[str, Any]:
        """Executes the complete segmentation pipeline."""
        seed_segment_rules(self.db)
        rfm_df = self.calculator.calculate_rfm()
        memberships = self.assign_segments(rfm_df)
        inserted, updated = self.persist_memberships_scd2(memberships)

        return {
            "total_customers": len(rfm_df),
            "memberships_created": inserted,
            "memberships_transitioned": updated,
            "memberships": memberships,
        }
