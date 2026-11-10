"""
System Evaluation Metrics Reconciliation Tool.
Directly calculates coverage, eligibility, suppression, and anomaly benchmark metrics from SQLite.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tabulate import tabulate
from src.database.database import DatabaseManager
from src.dashboard.metrics import DashboardMetrics


def audit_evaluation_metrics() -> None:
    db = DatabaseManager()
    metrics_engine = DashboardMetrics(db=db)

    print("\n" + "=" * 80)
    print("DATABASE AUDIT: SYSTEM EVALUATION METRICS RECONCILIATION")
    print("=" * 80)

    eval_data = metrics_engine.get_evaluation_metrics()
    bm = eval_data["benchmark"]

    # 1. Operational Ratios
    summary_ratios = [
        ["Segment Coverage Rate", f"{eval_data['segment_coverage_pct']}%", "Must be 100.0% (Zero unassigned customers)"],
        ["Recommendation Eligibility Rate", f"{eval_data['recommendation_eligibility_rate']}%", "Actions passed all consent & ticket filters"],
        ["Recommendation Suppression Rate", f"{eval_data['suppression_rate']}%", "Actions blocked by opt-outs or open complaints"],
        ["Campaign Conversion Rate", f"{eval_data['campaign_conversion_rate']}%", "Attributed orders / total sent actions"],
        ["Total Attributed Revenue", f"${eval_data['attributed_revenue']:,.2f}", "Net revenue from attributed orders"],
    ]

    print("\n[OPERATIONAL METRICS SUMMARY]")
    print(tabulate(summary_ratios, headers=["Evaluation Metric", "Calculated Score", "Benchmarking Standard"], tablefmt="fancy_grid"))

    # 2. Confusion Matrix & Anomaly Benchmarking
    benchmark_table = [
        ["Injected Anomalies (Ground Truth)", bm["ground_truth_count"]],
        ["Independent SQL Detections", bm["detected_count"]],
        ["True Positives (TP)", bm["true_positives"]],
        ["False Positives (FP)", bm["false_positives"]],
        ["False Negatives (FN)", bm["false_negatives"]],
        ["Precision Score", f"{bm['precision'] * 100:.1f}%"],
        ["Recall Score", f"{bm['recall'] * 100:.1f}%"],
        ["F1-Score", f"{bm['f1_score'] * 100:.1f}%"],
    ]

    print("\n[ANOMALY DETECTION BENCHMARK (PRECISION & RECALL)]")
    print(tabulate(benchmark_table, headers=["Benchmark Indicator", "Score"], tablefmt="fancy_grid"))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    audit_evaluation_metrics()
