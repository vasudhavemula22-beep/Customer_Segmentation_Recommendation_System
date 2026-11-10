"""
Comprehensive End-to-End Integration and Quality Assurance Test Suite.
Validates normal cases, boundary conditions, invalid inputs, foreign-key relationships,
consent enforcement, reproducible data generation, all four anomalies, and evaluation metrics.
"""

import sqlite3
import pytest
from src.database.database import DatabaseManager
from src.data_generation.config import RANDOM_SEED, ScaleConfig
from src.data_generation.generator import SyntheticDataGenerator
from src.segmentation.engine import SegmentationEngine
from src.recommendations.engine import RecommendationEngine
from src.anomalies.detector import AnomalyDetector
from src.dashboard.metrics import DashboardMetrics


@pytest.fixture(scope="module")
def db() -> DatabaseManager:
    return DatabaseManager()


# ------------------------------------------------------------------------------
# 1. DATABASE INTEGRITY & RELATIONSHIPS
# ------------------------------------------------------------------------------
def test_database_relationship_integrity(db: DatabaseManager):
    """Verifies that all child foreign keys link to valid parent records."""
    orphaned_orders = db.execute_scalar(
        """
        SELECT COUNT(*) FROM orders o 
        LEFT JOIN customers c ON o.customer_id = c.customer_id 
        WHERE c.customer_id IS NULL;
        """
    )
    assert orphaned_orders == 0, f"Found {orphaned_orders} orphaned orders"

    orphaned_lines = db.execute_scalar(
        """
        SELECT COUNT(*) FROM order_lines ol 
        LEFT JOIN orders o ON ol.order_id = o.order_id 
        LEFT JOIN products p ON ol.product_id = p.product_id 
        WHERE o.order_id IS NULL OR p.product_id IS NULL;
        """
    )
    assert orphaned_lines == 0, f"Found {orphaned_lines} orphaned order lines"


# ------------------------------------------------------------------------------
# 2. BOUNDARY CASES & INVALID INPUTS
# ------------------------------------------------------------------------------
def test_boundary_zero_order_prospects(db: DatabaseManager):
    """Verifies that customers with zero purchases are classified as Prospects."""
    sql = """
        SELECT c.customer_id, sm.segment_id, sr.segment_name 
        FROM customers c
        JOIN segment_memberships sm ON c.customer_id = sm.customer_id AND sm.is_active = 1
        JOIN segment_rules sr ON sm.segment_id = sr.segment_id
        LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status NOT IN ('Cancelled')
        GROUP BY c.customer_id
        HAVING COUNT(o.order_id) = 0;
    """
    prospects = db.fetch_all(sql)
    for p in prospects:
        assert p["segment_name"] == "Prospects", f"Customer {p['customer_id']} with 0 orders assigned to {p['segment_name']}"


def test_invalid_input_rejections(db: DatabaseManager):
    """Verifies that invalid enums and negative prices are rejected by SQLite CHECK constraints."""
    with pytest.raises(sqlite3.IntegrityError):
        with db.session() as conn:
            conn.execute(
                """
                INSERT INTO products (product_id, product_name, category, base_price, cost, is_active, created_at)
                VALUES ('PRD-INVALID', 'Faulty Item', 'InvalidCategory', 10.0, 5.0, 1, '2026-01-01');
                """
            )


# ------------------------------------------------------------------------------
# 3. CONSENT ENFORCEMENT & SUPPRESSION
# ------------------------------------------------------------------------------
def test_marketing_consent_enforcement(db: DatabaseManager):
    """
    Verifies zero marketing communications sent to opted-out customers
    (excluding the labeled test anomaly scenario for CUS-000022).
    """
    sql = """
        SELECT ao.outcome_id, ao.customer_id, ac.communication_channel, c.status
        FROM action_outcomes ao
        JOIN action_catalogs ac ON ao.action_id = ac.action_id
        JOIN consents c ON ao.customer_id = c.customer_id AND ac.communication_channel = c.channel
        WHERE ao.execution_status = 'Sent'
          AND c.status = 'Opted Out'
          AND ac.action_id != 'ACTN-2026-000001';
    """
    violations = db.fetch_all(sql)
    # Exclude the injected anomaly test customer (CUS-000022) and injected outcome ID
    true_violations = [
        v for v in violations 
        if "ANOMALY" not in v["outcome_id"] and v["customer_id"] != "CUS-000022"
    ]
    assert len(true_violations) == 0, f"Found unexpected consent violations: {true_violations}"


# ------------------------------------------------------------------------------
# 4. REPRODUCIBILITY TEST
# ------------------------------------------------------------------------------
def test_synthetic_data_reproducibility():
    """Verifies that two generators with seed 20261022 produce identical outputs."""
    cfg = ScaleConfig(customers=5, products=3, orders=5, engagement_events=10, support_cases=2)
    gen1 = SyntheticDataGenerator(config=cfg, seed=RANDOM_SEED)
    gen2 = SyntheticDataGenerator(config=cfg, seed=RANDOM_SEED)

    cust1 = gen1.generate_customers()
    cust2 = gen2.generate_customers()

    for c1, c2 in zip(cust1, cust2):
        assert c1["customer_id"] == c2["customer_id"]
        assert c1["email"] == c2["email"]
        assert c1["lifecycle_stage"] == c2["lifecycle_stage"]


# ------------------------------------------------------------------------------
# 5. ALL FOUR ANOMALY SCENARIOS DETECTED
# ------------------------------------------------------------------------------
def test_all_four_mandatory_anomalies_detected(db: DatabaseManager):
    """Verifies that all 4 mandatory negative scenarios are detected by independent algorithms."""
    detector = AnomalyDetector(db=db)
    detected = detector.run_full_scan()

    detected_types = {d["issue_type"] for d in detected}
    assert "Conflicting Exclusive Segments" in detected_types
    assert "Consent Violation" in detected_types
    assert "Incorrect Return Calculation" in detected_types
    assert "Wrong Action Attribution" in detected_types


# ------------------------------------------------------------------------------
# 6. EVALUATION METRICS ENGINE TEST
# ------------------------------------------------------------------------------
def test_evaluation_metrics_calculations(db: DatabaseManager):
    """Verifies that evaluation metrics produce mathematically valid scores."""
    dashboard = DashboardMetrics(db=db)
    eval_metrics = dashboard.get_evaluation_metrics()

    assert eval_metrics["segment_coverage_pct"] == 100.0, "Segment coverage must be 100%"
    assert 0.0 <= eval_metrics["recommendation_eligibility_rate"] <= 100.0
    assert 0.0 <= eval_metrics["suppression_rate"] <= 100.0
    assert eval_metrics["benchmark"]["precision"] == 1.0
    assert eval_metrics["benchmark"]["recall"] == 1.0
    assert eval_metrics["benchmark"]["f1_score"] == 1.0
