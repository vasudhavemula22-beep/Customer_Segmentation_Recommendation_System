"""
Recommendation Rules, Consent Verification, and Suppression Evaluator.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from src.database.database import DatabaseManager


class RecommendationRulesEvaluator:
    """Evaluates customer eligibility, consent rights, and suppression criteria."""

    def __init__(self, db: DatabaseManager, anchor_date: datetime) -> None:
        self.db = db
        self.anchor_date = anchor_date

    def check_customer_consent(self, customer_id: str, channel: str) -> Tuple[bool, str]:
        """
        Verifies if the customer has an active 'Opted In' consent for the channel.
        Returns: (is_consented, explanation_message)
        """
        sql = """
            SELECT status FROM consents 
            WHERE customer_id = ? AND channel = ? AND is_active = 1
            ORDER BY updated_at DESC LIMIT 1;
        """
        status = self.db.execute_scalar(sql, (customer_id, channel))

        if status == "Opted In":
            return True, f"Active consent granted for {channel}."
        elif status == "Opted Out":
            return False, f"Suppressed: Customer withdrew marketing consent for {channel}."
        else:
            return False, f"Suppressed: No active consent record found for {channel}."

    def get_open_support_cases(self, customer_id: str) -> List[Dict[str, Any]]:
        """Retrieves unresolved support cases for the customer."""
        sql = """
            SELECT case_id, case_category, priority, status 
            FROM support_cases 
            WHERE customer_id = ? AND status IN ('Open', 'In Progress')
            ORDER BY CASE priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                ELSE 4 END ASC;
        """
        rows = self.db.fetch_all(sql, (customer_id,))
        return [dict(r) for r in rows]

    def check_fatigue_suppression(
        self, customer_id: str, action_id: str, channel: str, suppression_days: int
    ) -> Tuple[bool, str]:
        """
        Checks if customer was contacted with this action or channel within suppression_days.
        Returns: (is_suppressed, explanation_message)
        """
        cutoff_date = (self.anchor_date - timedelta(days=suppression_days)).strftime("%Y-%m-%d %H:%M:%S")

        sql = """
            SELECT executed_date FROM action_outcomes 
            WHERE customer_id = ? AND action_id = ? 
              AND execution_status = 'Sent' 
              AND executed_date >= ?
            ORDER BY executed_date DESC LIMIT 1;
        """
        last_executed = self.db.execute_scalar(sql, (customer_id, action_id, cutoff_date))

        if last_executed:
            return True, f"Suppressed: Frequency cap active (contacted on {last_executed}, suppression window: {suppression_days} days)."
        return False, "Not fatigue suppressed."
