"""
Recommendation Engine Database Verification Tool.
Audits recommendation distribution, consent enforcement, suppression breakdowns,
and financial conversion attribution.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tabulate import tabulate
from src.database.database import DatabaseManager


def audit_recommendations() -> None:
    db = DatabaseManager()

    print("\n" + "=" * 80)
    print("DATABASE AUDIT: ACTION RECOMMENDATIONS & SUPPRESSION LEDGER")
    print("=" * 80)

    # 1. Total Recommendations & Execution Status
    total_recs = db.execute_scalar("SELECT COUNT(*) FROM action_outcomes;")
    sent_cnt = db.execute_scalar("SELECT COUNT(*) FROM action_outcomes WHERE execution_status = 'Sent';")
    supp_cnt = db.execute_scalar("SELECT COUNT(*) FROM action_outcomes WHERE execution_status = 'Suppressed';")
    converted_cnt = db.execute_scalar("SELECT COUNT(*) FROM action_outcomes WHERE outcome_status = 'Converted';")
    attributed_rev = db.execute_scalar("SELECT COALESCE(SUM(conversion_value), 0.0) FROM action_outcomes;")

    print(f"Total Evaluated Recommendations : {total_recs:,}")
    print(f"Dispatched & Approved ('Sent')  : {sent_cnt:,} ({sent_cnt / total_recs * 100:.1f}%)")
    print(f"Blocked / Suppressed            : {supp_cnt:,} ({supp_cnt / total_recs * 100:.1f}%)")
    print(f"Total Converted Orders          : {converted_cnt:,}")
    print(f"Total Attributed Revenue        : ${attributed_rev:,.2f}")

    # 2. Action Breakdown Table
    action_sql = """
        SELECT 
            ac.action_id,
            ac.action_name,
            ac.communication_channel,
            COUNT(ao.outcome_id) as total_targeted,
            SUM(CASE WHEN ao.execution_status = 'Sent' THEN 1 ELSE 0 END) as sent_count,
            SUM(CASE WHEN ao.execution_status = 'Suppressed' THEN 1 ELSE 0 END) as suppressed_count,
            SUM(CASE WHEN ao.outcome_status = 'Converted' THEN 1 ELSE 0 END) as conversions,
            ROUND(COALESCE(SUM(ao.conversion_value), 0.0), 2) as revenue
        FROM action_catalogs ac
        LEFT JOIN action_outcomes ao ON ac.action_id = ao.action_id
        GROUP BY ac.action_id, ac.action_name, ac.communication_channel
        ORDER BY total_targeted DESC;
    """
    rows = db.fetch_all(action_sql)
    table_data = [
        [
            r["action_id"],
            r["action_name"],
            r["communication_channel"],
            f"{r['total_targeted']:,}",
            f"{r['sent_count']:,}",
            f"{r['suppressed_count']:,}",
            f"{r['conversions']:,}",
            f"${r['revenue']:,.2f}",
        ]
        for r in rows
    ]

    print("\n" + "=" * 80)
    print("ACTION DISPATCH & FINANCIAL PERFORMANCE BREAKDOWN")
    print("=" * 80)
    headers = ["Action ID", "Action Name", "Channel", "Targeted", "Sent", "Suppressed", "Conversions", "Revenue"]
    print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    audit_recommendations()
