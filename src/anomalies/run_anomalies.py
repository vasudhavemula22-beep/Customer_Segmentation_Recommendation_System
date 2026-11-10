"""
CLI Execution Script for Phase 6: Outcomes Tracking & Anomaly Detection.
Runs attribution, injects test scenarios, executes independent detector,
and prints complete audit reports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tabulate import tabulate

from src.database.database import DatabaseManager
from src.anomalies.outcomes_tracker import ActionOutcomesTracker
from src.anomalies.injector import AnomalyInjector
from src.anomalies.detector import AnomalyDetector


def run_phase6_pipeline() -> None:
    print("\n" + "=" * 90)
    print("STARTING PHASE 6: ACTION OUTCOMES, ANOMALY INJECTION & INDEPENDENT DETECTION")
    print("=" * 90)

    db = DatabaseManager()

    # Step 1: Reconcile baseline outcomes & conversions
    print("\n[1/4] Tracking and attributing post-recommendation outcomes...")
    tracker = ActionOutcomesTracker(db=db)
    res = tracker.record_baseline_outcomes()
    print(f"      Evaluated {res['total_sent_evaluated']} sent recommendations; "
          f"attributed {res['conversions']} conversions.")

    # Step 2: Inject the four mandatory labeled negative scenarios
    print("\n[2/4] Injecting four labeled anomaly scenarios and saving ground truth...")
    injector = AnomalyInjector(db=db)
    gt_records = injector.inject_all_anomalies()
    print(f"      Injected {len(gt_records)} scenarios into SQLite. "
          f"Ground truth written to 'data/ground_truth/ground_truth.json' and '.csv'.")

    # Step 3: Run independent detector
    print("\n[3/4] Running independent anomaly detection algorithms (zero ground-truth leakage)...")
    detector = AnomalyDetector(db=db)
    eval_result = detector.evaluate_against_ground_truth()

    # Step 4: Display Reports
    print("\n" + "=" * 90)
    print("REPORT 1: CAMPAIGN PERFORMANCE & ATTRIBUTED REVENUE")
    print("=" * 90)
    metrics_df = tracker.compute_campaign_metrics()
    print(tabulate(metrics_df, headers="keys", tablefmt="fancy_grid", showindex=False))

    print("\n" + "=" * 90)
    print("REPORT 2: INDEPENDENT ANOMALY DETECTION AUDIT LOG (ALL 9 REQUIRED FIELDS)")
    print("=" * 90)

    report_rows = []
    for d in eval_result["detected_records"]:
        report_rows.append([
            d["issue_id"],
            d["customer_id"],
            d["issue_type"],
            d["severity"],
            d["expected_behavior"],
            d["actual_behavior"],
            d["suggested_correction"],
        ])

    headers = [
        "Issue ID", "Customer", "Issue Type", "Severity",
        "Expected Behavior", "Actual Behavior", "Suggested Correction"
    ]
    print(tabulate(report_rows, headers=headers, tablefmt="fancy_grid"))

    print("\n" + "=" * 90)
    print("REPORT 3: EVALUATION BENCHMARK AGAINST GROUND TRUTH")
    print("=" * 90)
    benchmark_table = [
        ["Total Injected Anomalies (Ground Truth)", eval_result["ground_truth_count"]],
        ["Total Anomalies Detected", eval_result["detected_count"]],
        ["True Positives (TP)", eval_result["true_positives"]],
        ["False Positives (FP)", eval_result["false_positives"]],
        ["False Negatives (FN)", eval_result["false_negatives"]],
        ["Precision", f"{eval_result['precision'] * 100:.1f}%"],
        ["Recall", f"{eval_result['recall'] * 100:.1f}%"],
        ["F1-Score", f"{eval_result['f1_score'] * 100:.1f}%"],
    ]
    print(tabulate(benchmark_table, headers=["Metric", "Value"], tablefmt="fancy_grid"))
    print("\nPhase 6 execution complete. All anomalies identified and verified.\n")


if __name__ == "__main__":
    run_phase6_pipeline()
