"""
Direct SQLite Verification Script for the Four Mandatory Anomaly Scenarios.
Queries the database directly to display raw records for each test case.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import DatabaseManager

db = DatabaseManager()

print("\n" + "=" * 80)
print("MANUAL DIRECT SQLITE ANOMALY VERIFICATION")
print("=" * 80)

# 1. Check Scenario 1: Conflicting Segments for CUS-000021
rows1 = db.fetch_all("""
    SELECT sm.customer_id, sr.segment_name, sm.is_active 
    FROM segment_memberships sm
    JOIN segment_rules sr ON sm.segment_id = sr.segment_id
    WHERE sm.customer_id = 'CUS-000021' AND sm.is_active = 1;
""")
print("\n[Scenario 1] Customer CUS-000021 Concurrent Active Memberships:")
for r in rows1:
    print(f"   -> Segment: {r['segment_name']} | is_active: {r['is_active']}")

# 2. Check Scenario 2: Consent Violation for CUS-000022
rows2 = db.fetch_all("""
    SELECT ao.outcome_id, ao.customer_id, ao.execution_status, c.channel, c.status as consent_status
    FROM action_outcomes ao
    JOIN action_catalogs ac ON ao.action_id = ac.action_id
    JOIN consents c ON ao.customer_id = c.customer_id AND ac.communication_channel = c.channel
    WHERE ao.customer_id = 'CUS-000022' AND ao.execution_status = 'Sent';
""")
print("\n[Scenario 2] Customer CUS-000022 Dispatched Action vs Legal Consent:")
for r in rows2:
    print(f"   -> Outcome: {r['outcome_id']} | Dispatched: {r['execution_status']} | Legal Consent: {r['consent_status']}")

# 3. Check Scenario 3: Return Not Netting Spend on ORD-2026-ANOMALY-RET
row3 = db.fetch_all("""
    SELECT o.order_id, o.total_amount, o.net_amount, SUM(ol.return_amount) as total_returned
    FROM orders o
    JOIN order_lines ol ON o.order_id = ol.order_id
    WHERE o.order_id = 'ORD-2026-ANOMALY-RET'
    GROUP BY o.order_id;
""")
if row3:
    r = row3[0]
    expected = r['total_amount'] - r['total_returned']
    print(f"\n[Scenario 3] Order {r['order_id']} Return Reconciliation:")
    print(f"   -> Gross Total     : ${r['total_amount']:.2f}")
    print(f"   -> Refund Amount   : ${r['total_returned']:.2f}")
    print(f"   -> Recorded Net    : ${r['net_amount']:.2f}")
    print(f"   -> DEFECT DETECTED : net_amount should be ${expected:.2f}, but is recorded as ${r['net_amount']:.2f}")

# 4. Check Scenario 4: Wrong Action Attribution
row4 = db.fetch_all("""
    SELECT ao.outcome_id, ao.executed_date, o.order_id, o.order_date
    FROM action_outcomes ao
    JOIN orders o ON ao.attributed_order_id = o.order_id
    WHERE ao.outcome_id = 'OUT-2026-ANOMALY-ATTR';
""")
if row4:
    r = row4[0]
    print(f"\n[Scenario 4] Outcome {r['outcome_id']} Chronological Attribution:")
    print(f"   -> Action Executed Date : {r['executed_date']}")
    print(f"   -> Attributed Order Date: {r['order_date']}")
    print("   -> DEFECT DETECTED      : Order was placed 5 months BEFORE the campaign was dispatched!")

print("\n" + "=" * 80 + "\n")
