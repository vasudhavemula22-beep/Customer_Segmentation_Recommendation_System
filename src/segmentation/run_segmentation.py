"""
CLI Execution Script for Customer Segmentation Engine.
Runs RFM computation, rule assignment, SCD Type 2 persistence, and displays reports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collections import Counter
import pandas as pd
from tabulate import tabulate

from src.database.database import DatabaseManager
from src.segmentation.engine import SegmentationEngine


def run_segmentation_pipeline() -> None:
    print("\n" + "=" * 75)
    print("STARTING EXPLAINABLE CUSTOMER SEGMENTATION ENGINE")
    print("=" * 75)

    db = DatabaseManager()
    engine = SegmentationEngine(db=db)
    
    result = engine.execute_segmentation_run()
    memberships = result["memberships"]

    print(f"\nTotal Evaluated Customers: {result['total_customers']}")
    print(f"New Memberships Inserted : {result['memberships_created']}")
    print(f"Historical Transitions   : {result['memberships_transitioned']}\n")

    # 1. Segment Distribution Summary
    counts = Counter(m["segment_name"] for m in memberships)
    
    summary_data = []
    # Fetch segment rules metadata to display thresholds alongside counts
    rules = engine._fetch_active_rules()
    for rule in rules:
        name = rule["segment_name"]
        cnt = counts.get(name, 0)
        pct = (cnt / len(memberships)) * 100 if memberships else 0.0
        summary_data.append([
            rule["segment_id"],
            name,
            f"{cnt} ({pct:.1f}%)",
            f"R<={rule['max_recency_days']}d | F>={rule['min_frequency']} | M>=${rule['min_monetary']:.0f}",
            rule["description"]
        ])

    print("=" * 75)
    print("CUSTOMER SEGMENT DISTRIBUTION REPORT")
    print("=" * 75)
    headers = ["Segment ID", "Segment Name", "Customer Count", "RFM Thresholds", "Business Definition"]
    print(tabulate(summary_data, headers=headers, tablefmt="fancy_grid"))

    # 2. Sample Customer Explanations
    print("\n" + "=" * 75)
    print("SAMPLE EXPLAINABLE CUSTOMER ASSIGNMENTS")
    print("=" * 75)

    sample_customers = memberships[:6]
    sample_rows = []
    for s in sample_customers:
        sample_rows.append([
            s["customer_id"],
            s["segment_name"],
            f"{s['recency_days']} days",
            s["frequency"],
            f"${s['monetary']:.2f}",
            s["assignment_reason"]
        ])

    sample_headers = ["Customer ID", "Assigned Segment", "Recency", "Frequency", "Net Spend", "Explainable Reason"]
    print(tabulate(sample_rows, headers=sample_headers, tablefmt="fancy_grid"))
    print("\nSegmentation complete. All memberships persisted in 'segment_memberships' table.\n")


if __name__ == "__main__":
    run_segmentation_pipeline()
