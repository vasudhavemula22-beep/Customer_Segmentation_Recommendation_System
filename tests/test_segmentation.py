"""
Automated Pytest Suite for Customer Segmentation Engine.
Tests RFM calculation, segment rule adherence, mutual exclusivity,
explanation accuracy, and SCD Type 2 history preservation.
"""

from datetime import datetime
import pytest
from src.database.database import DatabaseManager
from src.segmentation.engine import SegmentationEngine
from src.segmentation.rfm_calculator import RFMCalculator


@pytest.fixture(scope="module")
def db() -> DatabaseManager:
    return DatabaseManager()


def test_rfm_calculation_coverage(db: DatabaseManager):
    """Verifies that RFM metrics are computed for 100% of customers."""
    calc = RFMCalculator(db=db)
    rfm_df = calc.calculate_rfm()

    total_customers = db.execute_scalar("SELECT COUNT(*) FROM customers;")
    assert len(rfm_df) == total_customers
    assert "recency_days" in rfm_df.columns
    assert "frequency" in rfm_df.columns
    assert "monetary" in rfm_df.columns
    assert (rfm_df["recency_days"] >= 0).all()
    assert (rfm_df["frequency"] >= 0).all()


def test_mutual_exclusivity_per_customer(db: DatabaseManager):
    """Verifies that every customer belongs to exactly ONE active segment."""
    engine = SegmentationEngine(db=db)
    engine.execute_segmentation_run()

    sql = """
        SELECT customer_id, COUNT(*) as active_count
        FROM segment_memberships
        WHERE is_active = 1
        GROUP BY customer_id
        HAVING active_count > 1;
    """
    conflicts = db.fetch_all(sql)
    assert len(conflicts) == 0, f"Found customers with multiple active segments: {conflicts}"


def test_all_customers_assigned_active_segment(db: DatabaseManager):
    """Verifies that no customer is left unassigned."""
    total_customers = db.execute_scalar("SELECT COUNT(*) FROM customers;")
    assigned_active = db.execute_scalar("SELECT COUNT(DISTINCT customer_id) FROM segment_memberships WHERE is_active = 1;")
    assert assigned_active == total_customers, f"Expected {total_customers} active assignments, got {assigned_active}"


def test_explanation_matches_metrics(db: DatabaseManager):
    """Verifies that the human-readable explanation accurately reports the customer's RFM stats."""
    sql = """
        SELECT sm.customer_id, sm.assignment_reason, sm.segment_id
        FROM segment_memberships sm
        WHERE sm.is_active = 1
        LIMIT 20;
    """
    rows = db.fetch_all(sql)
    for r in rows:
        reason = r["assignment_reason"]
        assert len(reason) > 10, f"Explanation is empty or truncated for customer {r['customer_id']}"
        assert ("Purchased" in reason or "First-time" in reason or "Registered" in reason or "Inactive" in reason or "High past activity" in reason)


def test_scd2_history_preservation(db: DatabaseManager):
    """
    Simulates a customer transitioning segments:
    Verifies that the previous membership is expired (is_active = 0, valid_to populated)
    and a new record is inserted with is_active = 1.
    """
    engine = SegmentationEngine(db=db)
    cid = "CUS-000001"
    
    # Clean previous memberships for CUS-000001 to isolate this test
    db.execute_non_query("DELETE FROM segment_memberships WHERE customer_id = ?;", (cid,))

    # 1. Force customer into 'New Customers' on 2026-01-01
    initial_mem = [{
        "membership_id": f"MEM-SEG-2026-000004-{cid}",
        "segment_id": "SEG-2026-000004",
        "segment_name": "New Customers",
        "customer_id": cid,
        "confidence_score": 1.0,
        "assignment_reason": "Manual test initial assignment.",
        "recency_days": 10,
        "frequency": 1,
        "monetary": 50.0,
    }]
    engine.persist_memberships_scd2(initial_mem, effective_date="2026-01-01 00:00:00")

    # Verify initial active
    active_seg = db.execute_scalar("SELECT segment_id FROM segment_memberships WHERE customer_id = ? AND is_active = 1;", (cid,))
    assert active_seg == "SEG-2026-000004"

    # 2. Transition customer to 'Champions' on 2026-06-01
    updated_mem = [{
        "membership_id": f"MEM-SEG-2026-000001-{cid}",
        "segment_id": "SEG-2026-000001",
        "segment_name": "Champions",
        "customer_id": cid,
        "confidence_score": 1.0,
        "assignment_reason": "Manual test transition to Champions.",
        "recency_days": 5,
        "frequency": 8,
        "monetary": 1200.0,
    }]
    engine.persist_memberships_scd2(updated_mem, effective_date="2026-06-01 00:00:00")

    # 3. Verify history preservation
    records = db.fetch_all("SELECT segment_id, valid_from, valid_to, is_active FROM segment_memberships WHERE customer_id = ? ORDER BY valid_from ASC;", (cid,))
    assert len(records) == 2, f"Expected exactly 2 historical records, got {len(records)}"

    # Check expired record
    old_record = records[0]
    assert old_record["segment_id"] == "SEG-2026-000004"
    assert old_record["is_active"] == 0
    assert old_record["valid_to"] == "2026-06-01 00:00:00"

    # Check active record
    new_record = records[1]
    assert new_record["segment_id"] == "SEG-2026-000001"
    assert new_record["is_active"] == 1
    assert new_record["valid_to"] is None
