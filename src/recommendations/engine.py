"""
Action Recommendation Engine.
Produces explainable, rule-based business recommendations, enforces legal consent
and suppression logic, and persists recommendations in action_outcomes.
Optimized with in-memory preloading for sub-second execution on 50,000 customers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

from src.database.database import DatabaseManager
from src.recommendations.catalog import seed_action_catalog
from src.recommendations.rules import RecommendationRulesEvaluator

ANCHOR_DATE = datetime(2026, 10, 22, 12, 0, 0)


class RecommendationEngine:
    """Decision engine for customer next-best-actions."""

    def __init__(self, db: Optional[DatabaseManager] = None, anchor_date: datetime = ANCHOR_DATE) -> None:
        self.db = db or DatabaseManager()
        self.anchor_date = anchor_date
        self.rules_evaluator = RecommendationRulesEvaluator(db=self.db, anchor_date=self.anchor_date)

    def _fetch_customer_profiles(self) -> List[Dict[str, Any]]:
        """Fetches active segment membership, order metrics, and customer info."""
        sql = """
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                c.email,
                sm.segment_id,
                sr.segment_name,
                COUNT(o.order_id) as total_orders,
                COALESCE(SUM(o.net_amount), 0.0) as total_spend
            FROM customers c
            JOIN segment_memberships sm 
                ON c.customer_id = sm.customer_id AND sm.is_active = 1
            JOIN segment_rules sr 
                ON sm.segment_id = sr.segment_id
            LEFT JOIN orders o 
                ON c.customer_id = o.customer_id AND o.order_status NOT IN ('Cancelled')
            GROUP BY c.customer_id, sm.segment_id, sr.segment_name;
        """
        rows = self.db.fetch_all(sql)
        return [dict(r) for r in rows]

    def _match_action(self, profile: Dict[str, Any], open_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Selects candidate action based on service priority and segment membership."""
        high_priority_cases = [c for c in open_cases if c["priority"] in ("Critical", "High")]
        if high_priority_cases:
            case = high_priority_cases[0]
            return {
                "action_id": "ACTN-2026-000001",
                "action_name": "Customer Support Follow-up",
                "channel": "Phone Call",
                "suppression_days": 3,
                "is_service_transactional": True,
                "base_reason": f"Customer has open {case['priority']} support case ({case['case_category']}).",
            }

        seg_name = profile["segment_name"]

        if seg_name == "Champions":
            return {
                "action_id": "ACTN-2026-000002",
                "action_name": "Premium Customer Benefit",
                "channel": "Email",
                "suppression_days": 14,
                "is_service_transactional": False,
                "base_reason": "High-value Champion; eligible for exclusive VIP concierge benefits.",
            }
        elif seg_name == "Loyal Customers":
            return {
                "action_id": "ACTN-2026-000003",
                "action_name": "Loyalty Reward",
                "channel": "Email",
                "suppression_days": 14,
                "is_service_transactional": False,
                "base_reason": "Consistent repeat purchaser; eligible for double reward points voucher.",
            }
        elif seg_name in ("Potential Loyalists", "At Risk"):
            return {
                "action_id": "ACTN-2026-000004",
                "action_name": "Discount Offer",
                "channel": "Email",
                "suppression_days": 14,
                "is_service_transactional": False,
                "base_reason": f"Customer in {seg_name}; eligible for 15% incentive coupon.",
            }
        elif seg_name == "Dormant Customers":
            return {
                "action_id": "ACTN-2026-000005",
                "action_name": "Re-engagement Campaign",
                "channel": "SMS",
                "suppression_days": 30,
                "is_service_transactional": False,
                "base_reason": "Inactive over 180 days; targeted with win-back SMS reactivation.",
            }
        else:
            return {
                "action_id": "ACTN-2026-000006",
                "action_name": "Welcome Message",
                "channel": "Email",
                "suppression_days": 7,
                "is_service_transactional": False,
                "base_reason": f"Account in {seg_name}; eligible for welcome onboarding and orientation.",
            }

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Evaluates customer profiles using bulk in-memory maps for sub-second execution."""
        profiles = self._fetch_customer_profiles()
        recommendations: List[Dict[str, Any]] = []

        now_str = self.anchor_date.strftime("%Y-%m-%d %H:%M:%S")

        # Preload open support cases into a dictionary: customer_id -> list of cases
        cases_sql = """
            SELECT customer_id, case_id, case_category, priority, status 
            FROM support_cases 
            WHERE status IN ('Open', 'In Progress')
            ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END ASC;
        """
        all_cases = self.db.fetch_all(cases_sql)
        cases_map: Dict[str, List[Dict[str, Any]]] = {}
        for c in all_cases:
            cases_map.setdefault(c["customer_id"], []).append(dict(c))

        # Preload active consents: (customer_id, channel) -> status
        consents_sql = "SELECT customer_id, channel, status FROM consents WHERE is_active = 1;"
        all_consents = self.db.fetch_all(consents_sql)
        consents_map: Dict[tuple[str, str], str] = {
            (c["customer_id"], c["channel"]): c["status"] for c in all_consents
        }

        current_max = self.db.execute_scalar("SELECT COUNT(*) FROM action_outcomes;") or 0
        counter = current_max + 1

        for prof in profiles:
            cid = prof["customer_id"]
            open_cases = cases_map.get(cid, [])
            action = self._match_action(prof, open_cases)

            # BRANCH A: TRANSACTIONAL SERVICE REMEDIATION
            if action.get("is_service_transactional", False):
                recs_record = {
                    "outcome_id": f"OUT-2026-{str(counter).zfill(6)}",
                    "customer_id": cid,
                    "customer_name": f"{prof['first_name']} {prof['last_name']}",
                    "segment_name": prof["segment_name"],
                    "action_id": action["action_id"],
                    "action_name": action["action_name"],
                    "channel": action["channel"],
                    "eligibility_status": "Eligible",
                    "execution_status": "Sent",
                    "executed_date": now_str,
                    "decision_reason": f"Approved: {action['base_reason']} Proactive service follow-up scheduled.",
                    "recommended_date": now_str,
                }
                recommendations.append(recs_record)
                counter += 1
                continue

            # BRANCH B: MARKETING & PROMOTIONAL ACTIONS
            # 1. Legal Consent Check
            channel_consent = consents_map.get((cid, action["channel"]))
            if channel_consent == "Opted Out":
                recs_record = {
                    "outcome_id": f"OUT-2026-{str(counter).zfill(6)}",
                    "customer_id": cid,
                    "customer_name": f"{prof['first_name']} {prof['last_name']}",
                    "segment_name": prof["segment_name"],
                    "action_id": action["action_id"],
                    "action_name": action["action_name"],
                    "channel": action["channel"],
                    "eligibility_status": "Suppressed",
                    "execution_status": "Suppressed",
                    "executed_date": None,
                    "decision_reason": f"Suppressed: Customer withdrew marketing consent for {action['channel']}.",
                    "recommended_date": now_str,
                }
                recommendations.append(recs_record)
                counter += 1
                continue
            elif channel_consent != "Opted In":
                recs_record = {
                    "outcome_id": f"OUT-2026-{str(counter).zfill(6)}",
                    "customer_id": cid,
                    "customer_name": f"{prof['first_name']} {prof['last_name']}",
                    "segment_name": prof["segment_name"],
                    "action_id": action["action_id"],
                    "action_name": action["action_name"],
                    "channel": action["channel"],
                    "eligibility_status": "Suppressed",
                    "execution_status": "Suppressed",
                    "executed_date": None,
                    "decision_reason": f"Suppressed: No active consent record found for {action['channel']}.",
                    "recommended_date": now_str,
                }
                recommendations.append(recs_record)
                counter += 1
                continue

            # 2. Support Ticket Suppression
            if len(open_cases) > 0:
                recs_record = {
                    "outcome_id": f"OUT-2026-{str(counter).zfill(6)}",
                    "customer_id": cid,
                    "customer_name": f"{prof['first_name']} {prof['last_name']}",
                    "segment_name": prof["segment_name"],
                    "action_id": action["action_id"],
                    "action_name": action["action_name"],
                    "channel": action["channel"],
                    "eligibility_status": "Suppressed",
                    "execution_status": "Suppressed",
                    "executed_date": None,
                    "decision_reason": f"Suppressed: Customer has active open support ticket ({open_cases[0]['case_category']}). Marketing paused.",
                    "recommended_date": now_str,
                }
                recommendations.append(recs_record)
                counter += 1
                continue

            # 3. Approved
            recs_record = {
                "outcome_id": f"OUT-2026-{str(counter).zfill(6)}",
                "customer_id": cid,
                "customer_name": f"{prof['first_name']} {prof['last_name']}",
                "segment_name": prof["segment_name"],
                "action_id": action["action_id"],
                "action_name": action["action_name"],
                "channel": action["channel"],
                "eligibility_status": "Eligible",
                "execution_status": "Sent",
                "executed_date": now_str,
                "decision_reason": f"Approved: {action['base_reason']} Active consent granted for {action['channel']}.",
                "recommended_date": now_str,
            }
            recommendations.append(recs_record)
            counter += 1

        return recommendations

    def persist_recommendations(self, recommendations: List[Dict[str, Any]], batch_size: int = 5000) -> int:
        """Appends recommendations into action_outcomes in high-speed batches."""
        now_str = self.anchor_date.strftime("%Y-%m-%d %H:%M:%S")
        sql = """
            INSERT INTO action_outcomes (
                outcome_id, action_id, customer_id,
                recommended_date, executed_date, execution_status,
                outcome_status, conversion_value, attribution_confidence, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'Pending', 0.0, 1.0, ?);
        """
        with self.db.session() as conn:
            cursor = conn.cursor()
            for i in range(0, len(recommendations), batch_size):
                batch = recommendations[i : i + batch_size]
                payload = [
                    (
                        r["outcome_id"],
                        r["action_id"],
                        r["customer_id"],
                        r["recommended_date"],
                        r["executed_date"],
                        r["execution_status"],
                        now_str,
                    )
                    for r in batch
                ]
                cursor.executemany(sql, payload)
        return len(recommendations)

    def execute_recommendation_run(self) -> Dict[str, Any]:
        """Runs action catalog seeding, decision engine, and outcome persistence."""
        seed_action_catalog(self.db)
        recs = self.generate_recommendations()
        count = self.persist_recommendations(recs)
        return {
            "total_evaluated": len(recs),
            "approved_count": sum(1 for r in recs if r["execution_status"] == "Sent"),
            "suppressed_count": sum(1 for r in recs if r["execution_status"] == "Suppressed"),
            "recommendations": recs,
        }
