"""
CLI Execution Script for Action Recommendation Engine.
Evaluates customers, applies consent & suppression rules, persists outcomes,
and displays detailed recommendation reports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collections import Counter
from tabulate import tabulate

from src.database.database import DatabaseManager
from src.recommendations.engine import RecommendationEngine


def run_recommendations_pipeline() -> None:
    print("\n" + "=" * 80)
    print("STARTING BUSINESS-RULE-BASED RECOMMENDATION ENGINE")
    print("=" * 80)

    db = DatabaseManager()
    engine = RecommendationEngine(db=db)
    result = engine.execute_recommendation_run()
    recs = result["recommendations"]

    print(f"\nTotal Evaluated Customers: {result['total_evaluated']}")
    print(f"Eligible & Dispatched (Sent) : {result['approved_count']}")
    print(f"Suppressed (Blocked)         : {result['suppressed_count']}\n")

    # 1. Action Dispatch Distribution Table
    action_counts = Counter(r["action_name"] for r in recs if r["execution_status"] == "Sent")
    suppressed_counts = Counter(r["action_name"] for r in recs if r["execution_status"] == "Suppressed")

    dist_rows = []
    all_actions = sorted(list(set(list(action_counts.keys()) + list(suppressed_counts.keys()))))
    for act in all_actions:
        sent = action_counts.get(act, 0)
        blocked = suppressed_counts.get(act, 0)
        total = sent + blocked
        dist_rows.append([act, sent, blocked, total])

    print("=" * 80)
    print("ACTION RECOMMENDATION DISPATCH SUMMARY")
    print("=" * 80)
    headers = ["Action Name", "Approved (Sent)", "Suppressed (Blocked)", "Total Targeted"]
    print(tabulate(dist_rows, headers=headers, tablefmt="fancy_grid"))

    # 2. Approved Recommendations Sample
    approved_sample = [r for r in recs if r["execution_status"] == "Sent"][:4]
    approved_rows = [
        [
            r["customer_id"],
            r["segment_name"],
            r["action_name"],
            r["channel"],
            r["eligibility_status"],
            r["decision_reason"],
        ]
        for r in approved_sample
    ]

    print("\n" + "=" * 80)
    print("SAMPLE APPROVED RECOMMENDATIONS (ELIGIBLE & SENT)")
    print("=" * 80)
    sample_headers = ["Customer ID", "Segment", "Recommended Action", "Channel", "Eligibility", "Decision Explanation"]
    print(tabulate(approved_rows, headers=sample_headers, tablefmt="fancy_grid"))

    # 3. Suppressed Recommendations Sample
    suppressed_sample = [r for r in recs if r["execution_status"] == "Suppressed"][:4]
    suppressed_rows = [
        [
            r["customer_id"],
            r["segment_name"],
            r["action_name"],
            r["channel"],
            r["eligibility_status"],
            r["decision_reason"],
        ]
        for r in suppressed_sample
    ]

    print("\n" + "=" * 80)
    print("SAMPLE BLOCKED / SUPPRESSED RECOMMENDATIONS (EXPLAINED)")
    print("=" * 80)
    print(tabulate(suppressed_rows, headers=sample_headers, tablefmt="fancy_grid"))
    print("\nRecommendations saved in 'action_outcomes' table successfully.\n")


if __name__ == "__main__":
    run_recommendations_pipeline()
