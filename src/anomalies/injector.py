"""
Controlled Anomaly Injection Engine and Ground Truth Generator.
Injects the four mandatory labeled negative scenarios into the database
and writes known benchmark answers to data/ground_truth/.
Auto-seeds segment_rules to prevent foreign-key reference errors.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

from src.database.database import DatabaseManager
from src.segmentation.segment_rules import seed_segment_rules


class AnomalyInjector:
    """Injects four distinct labeled anomaly scenarios for evaluation."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.ground_truth_dir = Path("data") / "ground_truth"
        self.ground_truth_dir.mkdir(parents=True, exist_ok=True)

    def inject_all_anomalies(self) -> List[Dict[str, Any]]:
        """Injects all 4 mandatory scenarios and records ground truth."""
        # Ensure rules exist in segment_rules first
        seed_segment_rules(self.db)
        ground_truth_records: List[Dict[str, Any]] = []

        # ----------------------------------------------------------------------
        # SCENARIO 1: Conflicting Exclusive Segments
        # Customer CUS-000021 gets assigned to TWO active exclusive segments:
        # 'Champions' (SEG-2026-000001) AND 'At Risk' (SEG-2026-000005)
        # ----------------------------------------------------------------------
        cid_1 = "CUS-000021"
        mem_id_conflict = f"MEM-SEG-2026-000005-{cid_1}-ANOMALY"

        with self.db.session() as conn:
            conn.execute(
                """
                INSERT INTO segment_memberships (
                    membership_id, segment_id, customer_id, assigned_date,
                    valid_from, valid_to, is_active, confidence_score, assignment_reason
                ) VALUES (?, 'SEG-2026-000001', ?, '2026-10-22 12:00:00',
                          '2026-10-22 12:00:00', NULL, 1, 1.0, 'Baseline assignment')
                ON CONFLICT(membership_id) DO UPDATE SET is_active = 1, valid_to = NULL;
                """,
                (f"MEM-SEG-2026-000001-{cid_1}", cid_1),
            )
            conn.execute(
                """
                INSERT INTO segment_memberships (
                    membership_id, segment_id, customer_id, assigned_date,
                    valid_from, valid_to, is_active, confidence_score, assignment_reason
                ) VALUES (?, 'SEG-2026-000005', ?, '2026-10-22 12:00:00',
                          '2026-10-22 12:00:00', NULL, 1, 1.0, 'INJECTED ANOMALY: Overlapping exclusive membership')
                ON CONFLICT(membership_id) DO UPDATE SET is_active = 1, valid_to = NULL;
                """,
                (mem_id_conflict, cid_1),
            )

        ground_truth_records.append({
            "issue_id": "ISS-2026-000001",
            "scenario_number": 1,
            "issue_type": "Conflicting Exclusive Segments",
            "customer_id": cid_1,
            "affected_table": "segment_memberships",
            "affected_pk": mem_id_conflict,
            "expected_behavior": "Customer must belong to exactly one active exclusive segment.",
            "actual_behavior": "Customer has 2 concurrent active memberships in mutually exclusive segments (Champions & At Risk).",
            "severity": "CRITICAL",
            "suggested_correction": "Expire redundant membership by setting is_active = 0 and populating valid_to.",
        })

        # ----------------------------------------------------------------------
        # SCENARIO 2: Consent Violation
        # ----------------------------------------------------------------------
        cid_2 = "CUS-000022"
        out_id_consent = "OUT-2026-ANOMALY-CONSENT"

        with self.db.session() as conn:
            conn.execute(
                """
                UPDATE consents 
                SET status = 'Opted Out', updated_at = '2026-05-01 00:00:00' 
                WHERE customer_id = ? AND channel = 'Email';
                """,
                (cid_2,),
            )
            conn.execute(
                """
                INSERT INTO action_outcomes (
                    outcome_id, action_id, customer_id, recommended_date,
                    executed_date, execution_status, outcome_status,
                    conversion_value, attribution_confidence, recorded_at
                ) VALUES (
                    ?, 'ACTN-2026-000004', ?, '2026-10-22 12:00:00',
                    '2026-10-22 12:00:00', 'Sent', 'Pending', 0.0, 1.0, '2026-10-22 12:00:00'
                ) ON CONFLICT(outcome_id) DO UPDATE SET execution_status = 'Sent';
                """,
                (out_id_consent, cid_2),
            )

        ground_truth_records.append({
            "issue_id": "ISS-2026-000002",
            "scenario_number": 2,
            "issue_type": "Consent Violation",
            "customer_id": cid_2,
            "affected_table": "action_outcomes",
            "affected_pk": out_id_consent,
            "expected_behavior": "Promotional communication must be Suppressed if customer has Opted Out.",
            "actual_behavior": "Marketing email action was executed ('Sent') to a customer with active Opted Out consent.",
            "severity": "CRITICAL",
            "suggested_correction": "Revoke execution, update status to 'Suppressed', and add consent withdrawal suppress note.",
        })

        # ----------------------------------------------------------------------
        # SCENARIO 3: Incorrect Return Calculation
        # ----------------------------------------------------------------------
        cid_3 = "CUS-000023"
        ord_id_return = "ORD-2026-ANOMALY-RET"
        line_id_return = "ORL-2026-ANOMALY-RET"

        with self.db.session() as conn:
            conn.execute(
                """
                INSERT INTO orders (
                    order_id, customer_id, order_date, order_status, channel,
                    subtotal_amount, discount_amount, tax_amount, total_amount, net_amount, created_at
                ) VALUES (
                    ?, ?, '2026-09-10 14:00:00', 'Returned', 'Web',
                    150.0, 0.0, 12.0, 162.0, 162.0, '2026-09-10 14:00:00'
                ) ON CONFLICT(order_id) DO UPDATE SET net_amount = 162.0;
                """,
                (ord_id_return, cid_3),
            )
            conn.execute(
                """
                INSERT INTO order_lines (
                    order_line_id, order_id, product_id, quantity, unit_price,
                    line_total, is_returned, return_amount, return_date, created_at
                ) VALUES (
                    ?, ?, 'PRD-000001', 1, 89.99, 89.99, 1, 89.99, '2026-09-15 10:00:00', '2026-09-10 14:00:00'
                ) ON CONFLICT(order_line_id) DO UPDATE SET return_amount = 89.99, is_returned = 1;
                """,
                (line_id_return, ord_id_return),
            )

        ground_truth_records.append({
            "issue_id": "ISS-2026-000003",
            "scenario_number": 3,
            "issue_type": "Incorrect Return Calculation",
            "customer_id": cid_3,
            "affected_table": "orders",
            "affected_pk": ord_id_return,
            "expected_behavior": "Order net_amount must equal total_amount minus return_amount ($162.00 - $89.99 = $72.01).",
            "actual_behavior": "Order net_amount remains $162.00; return refund of $89.99 was not subtracted.",
            "severity": "HIGH",
            "suggested_correction": "Recalculate orders.net_amount = total_amount - return_amount.",
        })

        # ----------------------------------------------------------------------
        # SCENARIO 4: Wrong Action Attribution
        # ----------------------------------------------------------------------
        cid_4 = "CUS-000024"
        out_id_attr = "OUT-2026-ANOMALY-ATTR"
        prior_order_id = "ORD-2026-ANOMALY-PRIOR"

        with self.db.session() as conn:
            conn.execute(
                """
                INSERT INTO orders (
                    order_id, customer_id, order_date, order_status, channel,
                    subtotal_amount, discount_amount, tax_amount, total_amount, net_amount, created_at
                ) VALUES (
                    ?, ?, '2026-05-01 10:00:00', 'Delivered', 'Web',
                    120.0, 0.0, 9.60, 129.60, 129.60, '2026-05-01 10:00:00'
                ) ON CONFLICT(order_id) DO NOTHING;
                """,
                (prior_order_id, cid_4),
            )
            conn.execute(
                """
                INSERT INTO action_outcomes (
                    outcome_id, action_id, customer_id, recommended_date,
                    executed_date, execution_status, outcome_status,
                    attributed_order_id, conversion_value, attribution_confidence, recorded_at
                ) VALUES (
                    ?, 'ACTN-2026-000003', ?, '2026-10-01 12:00:00',
                    '2026-10-01 12:00:00', 'Sent', 'Converted',
                    ?, 129.60, 1.0, '2026-10-02 12:00:00'
                ) ON CONFLICT(outcome_id) DO UPDATE SET attributed_order_id = excluded.attributed_order_id;
                """,
                (out_id_attr, cid_4, prior_order_id),
            )

        ground_truth_records.append({
            "issue_id": "ISS-2026-000004",
            "scenario_number": 4,
            "issue_type": "Wrong Action Attribution",
            "customer_id": cid_4,
            "affected_table": "action_outcomes",
            "affected_pk": out_id_attr,
            "expected_behavior": "Attributed conversion order must be placed after the action execution date.",
            "actual_behavior": f"Action executed on 2026-10-01 credited with order {prior_order_id} placed on 2026-05-01.",
            "severity": "HIGH",
            "suggested_correction": "Clear attributed_order_id and set outcome_status to 'Pending' or 'Opened'.",
        })

        json_path = self.ground_truth_dir / "ground_truth.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ground_truth_records, f, indent=2)

        csv_path = self.ground_truth_dir / "ground_truth.csv"
        pd.DataFrame(ground_truth_records).to_csv(csv_path, index=False)

        return ground_truth_records


if __name__ == "__main__":
    db_mgr = DatabaseManager()
    injector = AnomalyInjector(db=db_mgr)
    records = injector.inject_all_anomalies()
    print(f"Successfully injected {len(records)} controlled anomalies.")
