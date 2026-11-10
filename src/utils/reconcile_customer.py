"""
Customer 360 Database Verification Tool.
Inspects customer master details, RFM metrics, consents, and order totals.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import DatabaseManager


def inspect_customer(cid: str = "CUS-000004") -> None:
    db = DatabaseManager()

    print("\n" + "=" * 80)
    print(f"DATABASE RECONCILIATION FOR CUSTOMER: {cid}")
    print("=" * 80)

    # 1. Profile Details
    profile_rows = db.fetch_all(
        "SELECT first_name, last_name, lifecycle_stage, acquisition_channel, created_at FROM customers WHERE customer_id = ?;",
        (cid,),
    )
    if not profile_rows:
        print(f"Error: Customer {cid} not found in database.")
        return

    profile = profile_rows[0]

    # 2. Segment & Explanation
    seg_rows = db.fetch_all(
        """
        SELECT sr.segment_name, sm.assigned_date, sm.assignment_reason 
        FROM segment_memberships sm 
        JOIN segment_rules sr ON sm.segment_id = sr.segment_id 
        WHERE sm.customer_id = ? AND sm.is_active = 1;
        """,
        (cid,),
    )
    seg_name = seg_rows[0]["segment_name"] if seg_rows else "Unassigned"
    reason = seg_rows[0]["assignment_reason"] if seg_rows else "N/A"

    print(f"Customer ID     : {cid}")
    print(f"Full Name       : {profile['first_name']} {profile['last_name']}")
    print(f"Lifecycle Stage : {profile['lifecycle_stage']}")
    print(f"Acquisition     : {profile['acquisition_channel']}")
    print(f"Registered On   : {profile['created_at']}")
    print(f"Active Segment  : {seg_name}")
    print(f"Explain Reason  : {reason}\n")

    # 3. Orders & Spend
    ord_rows = db.fetch_all(
        """
        SELECT COUNT(*) as ord_cnt, COALESCE(SUM(total_amount), 0.0) as gross, COALESCE(SUM(net_amount), 0.0) as net
        FROM orders WHERE customer_id = ? AND order_status NOT IN ('Cancelled');
        """,
        (cid,),
    )
    ord_summary = ord_rows[0]
    print(f"Total Orders    : {ord_summary['ord_cnt']}")
    print(f"Gross Spend     : ${ord_summary['gross']:,.2f}")
    print(f"Net Spend       : ${ord_summary['net']:,.2f}")

    # 4. Consents
    consents = db.fetch_all(
        "SELECT channel, status FROM consents WHERE customer_id = ? AND is_active = 1 ORDER BY channel ASC;",
        (cid,),
    )
    print("\nCommunication Preferences (Consents):")
    for c in consents:
        print(f"  - {c['channel']:<18}: {c['status']}")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    cid_arg = sys.argv[1] if len(sys.argv) > 1 else "CUS-000004"
    inspect_customer(cid_arg)
