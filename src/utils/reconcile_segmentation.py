"""
Segmentation Engine Database Verification Tool.
Audits segment distribution, verifies 100% customer coverage, and checks mutual exclusivity.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tabulate import tabulate
from src.database.database import DatabaseManager


def audit_segmentation() -> None:
    db = DatabaseManager()

    print("\n" + "=" * 80)
    print("DATABASE AUDIT: RFM SEGMENTATION COVERAGE & EXCLUSIVITY")
    print("=" * 80)

    # 1. Total Customers vs Segmented
    total_customers = db.execute_scalar("SELECT COUNT(*) FROM customers;")
    active_memberships = db.execute_scalar("SELECT COUNT(*) FROM segment_memberships WHERE is_active = 1;")
    distinct_segmented = db.execute_scalar("SELECT COUNT(DISTINCT customer_id) FROM segment_memberships WHERE is_active = 1;")

    print(f"Total Customers in Database     : {total_customers:,}")
    print(f"Distinct Customers with Segment : {distinct_segmented:,} ({distinct_segmented / total_customers * 100:.1f}% Coverage)")
    print(f"Total Active Membership Records : {active_memberships:,}")

    # 2. Check for Overlapping Exclusive Segments (Anomaly Scenario 1)
    conflicts_sql = """
        SELECT sm.customer_id, GROUP_CONCAT(sr.segment_name, ' & ') as segments, COUNT(*) as cnt
        FROM segment_memberships sm
        JOIN segment_rules sr ON sm.segment_id = sr.segment_id
        WHERE sm.is_active = 1 AND sr.is_exclusive = 1
        GROUP BY sm.customer_id
        HAVING cnt > 1;
    """
    conflicts = db.fetch_all(conflicts_sql)
    if conflicts:
        print(f"\n[!] Detected Exclusive Segment Conflicts (Anomaly Scenario 1): {len(conflicts)} customer(s)")
        for c in conflicts:
            print(f"    - Customer: {c['customer_id']} is active in: {c['segments']}")
    else:
        print("\n[OK] Zero segment conflicts detected.")

    # 3. Segment Breakdown Table
    summary_sql = """
        SELECT 
            sr.segment_id,
            sr.segment_name,
            sr.priority_order,
            COUNT(sm.customer_id) as customer_count,
            ROUND(AVG(cr.recency), 1) as avg_recency,
            ROUND(AVG(cr.frequency), 1) as avg_orders,
            ROUND(AVG(cr.monetary), 2) as avg_net_spend
        FROM segment_rules sr
        LEFT JOIN segment_memberships sm ON sr.segment_id = sm.segment_id AND sm.is_active = 1
        LEFT JOIN (
            SELECT 
                c.customer_id,
                CAST(ROUND(JULIANDAY('2026-10-22 12:00:00') - JULIANDAY(COALESCE(MAX(o.order_date), c.created_at))) AS INTEGER) as recency,
                COUNT(o.order_id) as frequency,
                COALESCE(SUM(o.net_amount), 0.0) as monetary
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status NOT IN ('Cancelled')
            GROUP BY c.customer_id
        ) cr ON sm.customer_id = cr.customer_id
        GROUP BY sr.segment_id, sr.segment_name, sr.priority_order
        ORDER BY sr.priority_order ASC;
    """
    rows = db.fetch_all(summary_sql)
    table_data = [
        [
            r["segment_id"],
            r["segment_name"],
            r["priority_order"],
            f"{r['customer_count']:,}",
            f"{r['avg_recency']:.1f}d",
            f"{r['avg_orders']:.1f}",
            f"${r['avg_net_spend']:,.2f}",
        ]
        for r in rows
    ]

    print("\n" + "=" * 80)
    print("SEGMENT DISTRIBUTION AUDIT TABLE")
    print("=" * 80)
    headers = ["Segment ID", "Segment Name", "Priority", "Customers", "Avg Recency", "Avg Orders", "Avg Net Spend"]
    print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    audit_segmentation()
