"""
Independent Anomaly Detection Engine.
Detects the four mandatory negative scenarios via database integrity rules.
Never uses ground-truth labels as input features.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from src.database.database import DatabaseManager


class AnomalyDetector:
    """Independent validator detecting database anomalies and business rule violations."""

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or DatabaseManager()

    # --------------------------------------------------------------------------
    # DETECTOR 1: Conflicting Exclusive Segments
    # --------------------------------------------------------------------------
    def detect_conflicting_segments(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                sm.customer_id,
                GROUP_CONCAT(sm.membership_id, ', ') as membership_ids,
                GROUP_CONCAT(sr.segment_name, ' & ') as conflicting_segments,
                COUNT(sm.membership_id) as active_count
            FROM segment_memberships sm
            JOIN segment_rules sr ON sm.segment_id = sr.segment_id
            WHERE sm.is_active = 1 AND sr.is_exclusive = 1
            GROUP BY sm.customer_id
            HAVING active_count > 1;
        """
        rows = self.db.fetch_all(sql)
        findings = []
        for r in rows:
            findings.append({
                "issue_id": f"DET-SEG-{r['customer_id']}",
                "customer_id": r["customer_id"],
                "issue_type": "Conflicting Exclusive Segments",
                "affected_record": f"segment_memberships ({r['membership_ids']})",
                "expected_behavior": "Customer must belong to exactly one active exclusive segment.",
                "actual_behavior": f"Customer concurrently active in multiple exclusive segments: {r['conflicting_segments']}.",
                "detection_result": "FLAGGED",
                "severity": "CRITICAL",
                "suggested_correction": "Expire redundant membership by setting is_active = 0 and valid_to = now.",
            })
        return findings

    # --------------------------------------------------------------------------
    # DETECTOR 2: Consent Violations
    # --------------------------------------------------------------------------
    def detect_consent_violations(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                ao.outcome_id,
                ao.customer_id,
                ao.executed_date,
                ac.action_name,
                ac.communication_channel,
                c.status as consent_status
            FROM action_outcomes ao
            JOIN action_catalogs ac ON ao.action_id = ac.action_id
            JOIN consents c ON ao.customer_id = c.customer_id AND ac.communication_channel = c.channel
            WHERE ao.execution_status = 'Sent'
              AND c.status = 'Opted Out'
              AND c.is_active = 1
              AND ac.action_id != 'ACTN-2026-000001'; -- Exclude transactional service remediation
        """
        rows = self.db.fetch_all(sql)
        findings = []
        for r in rows:
            findings.append({
                "issue_id": f"DET-CON-{r['outcome_id']}",
                "customer_id": r["customer_id"],
                "issue_type": "Consent Violation",
                "affected_record": f"action_outcomes (outcome_id: {r['outcome_id']})",
                "expected_behavior": f"Marketing action via {r['communication_channel']} must be Suppressed when customer has Opted Out.",
                "actual_behavior": f"Action '{r['action_name']}' was dispatched ('Sent') on {r['executed_date']} despite active Opted Out consent.",
                "detection_result": "FLAGGED",
                "severity": "CRITICAL",
                "suggested_correction": "Update execution_status to 'Suppressed' and void dispatched campaign payload.",
            })
        return findings

    # --------------------------------------------------------------------------
    # DETECTOR 3: Incorrect Return Deductions
    # --------------------------------------------------------------------------
    def detect_incorrect_returns(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                o.order_id,
                o.customer_id,
                o.total_amount,
                o.net_amount,
                SUM(ol.return_amount) as total_returned
            FROM orders o
            JOIN order_lines ol ON o.order_id = ol.order_id
            WHERE ol.is_returned = 1
            GROUP BY o.order_id, o.customer_id, o.total_amount, o.net_amount
            HAVING ABS(o.net_amount - (o.total_amount - total_returned)) > 0.01;
        """
        rows = self.db.fetch_all(sql)
        findings = []
        for r in rows:
            expected_net = round(r["total_amount"] - r["total_returned"], 2)
            findings.append({
                "issue_id": f"DET-RET-{r['order_id']}",
                "customer_id": r["customer_id"],
                "issue_type": "Incorrect Return Calculation",
                "affected_record": f"orders (order_id: {r['order_id']})",
                "expected_behavior": f"Order net_amount must reflect total_amount minus return_amount (${expected_net:.2f}).",
                "actual_behavior": f"Recorded net_amount is ${r['net_amount']:.2f}; returned refund of ${r['total_returned']:.2f} was not subtracted.",
                "detection_result": "FLAGGED",
                "severity": "HIGH",
                "suggested_correction": f"Update orders SET net_amount = {expected_net:.2f} WHERE order_id = '{r['order_id']}';",
            })
        return findings

    # --------------------------------------------------------------------------
    # DETECTOR 4: Wrong Action Attribution
    # --------------------------------------------------------------------------
    def detect_wrong_attributions(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                ao.outcome_id,
                ao.customer_id as outcome_customer_id,
                ao.executed_date,
                ao.execution_status,
                o.order_id,
                o.customer_id as order_customer_id,
                o.order_date
            FROM action_outcomes ao
            JOIN orders o ON ao.attributed_order_id = o.order_id
            WHERE ao.attributed_order_id IS NOT NULL
              AND (
                  o.order_date < ao.executed_date -- Order occurred prior to action execution
                  OR ao.customer_id != o.customer_id -- Mismatched customer account
                  OR ao.execution_status != 'Sent' -- Attributed to an unsent/suppressed action
              );
        """
        rows = self.db.fetch_all(sql)
        findings = []
        for r in rows:
            reasons = []
            if r["order_date"] < r["executed_date"]:
                reasons.append(f"order date ({r['order_date']}) preceded action execution ({r['executed_date']})")
            if r["outcome_customer_id"] != r["order_customer_id"]:
                reasons.append(f"customer mismatch (action for {r['outcome_customer_id']}, order by {r['order_customer_id']})")
            if r["execution_status"] != "Sent":
                reasons.append(f"action was not Sent (status: {r['execution_status']})")

            findings.append({
                "issue_id": f"DET-ATTR-{r['outcome_id']}",
                "customer_id": r["outcome_customer_id"],
                "issue_type": "Wrong Action Attribution",
                "affected_record": f"action_outcomes (outcome_id: {r['outcome_id']})",
                "expected_behavior": "Attributed order must belong to same customer and occur within post-execution window.",
                "actual_behavior": f"Invalid attribution: {', '.join(reasons)}.",
                "detection_result": "FLAGGED",
                "severity": "HIGH",
                "suggested_correction": "Disassociate attributed_order_id and recompute campaign conversion revenue.",
            })
        return findings

    # --------------------------------------------------------------------------
    # COMPREHENSIVE SCAN
    # --------------------------------------------------------------------------
    def run_full_scan(self) -> List[Dict[str, Any]]:
        """Executes all 4 independent detection checks and consolidates reports."""
        all_issues: List[Dict[str, Any]] = []
        all_issues.extend(self.detect_conflicting_segments())
        all_issues.extend(self.detect_consent_violations())
        all_issues.extend(self.detect_incorrect_returns())
        all_issues.extend(self.detect_wrong_attributions())
        return all_issues

    def evaluate_against_ground_truth(self) -> Dict[str, Any]:
        """
        Benchmarks detection results against isolated ground_truth.json:
        Computes True Positives, False Positives, False Negatives, Precision, Recall, and F1.
        """
        gt_path = Path("data") / "ground_truth" / "ground_truth.json"
        if not gt_path.exists():
            raise FileNotFoundError("Ground truth file not found. Run injector first.")

        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

        detected = self.run_full_scan()

        gt_keys = set((item["issue_type"], item["customer_id"]) for item in ground_truth)
        det_keys = set((item["issue_type"], item["customer_id"]) for item in detected)

        true_positives = len(gt_keys.intersection(det_keys))
        false_positives = len(det_keys - gt_keys)
        false_negatives = len(gt_keys - det_keys)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "ground_truth_count": len(ground_truth),
            "detected_count": len(detected),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "detected_records": detected,
        }
