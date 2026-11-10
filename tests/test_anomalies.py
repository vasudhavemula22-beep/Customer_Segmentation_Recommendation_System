"""
Automated Pytest Suite for Anomaly Detection Engine.
Validates independent identification of the four mandatory negative scenarios
and verifies benchmark precision and recall against ground truth.
"""

import pytest
from src.database.database import DatabaseManager
from src.anomalies.injector import AnomalyInjector
from src.anomalies.detector import AnomalyDetector


@pytest.fixture(scope="module")
def setup_anomalies():
    """Sets up database with injected anomalies and ground truth for testing."""
    db = DatabaseManager()
    injector = AnomalyInjector(db=db)
    injector.inject_all_anomalies()
    detector = AnomalyDetector(db=db)
    return db, detector


def test_detect_conflicting_exclusive_segments(setup_anomalies):
    """Verifies that Scenario 1 (Conflicting Exclusive Segments) is detected."""
    _, detector = setup_anomalies
    findings = detector.detect_conflicting_segments()
    assert len(findings) >= 1, "Failed to detect conflicting exclusive segments"
    target_customers = [f["customer_id"] for f in findings]
    assert "CUS-000021" in target_customers
    assert findings[0]["severity"] == "CRITICAL"


def test_detect_consent_violation(setup_anomalies):
    """Verifies that Scenario 2 (Consent Violation) is detected."""
    _, detector = setup_anomalies
    findings = detector.detect_consent_violations()
    assert len(findings) >= 1, "Failed to detect consent violation"
    target_customers = [f["customer_id"] for f in findings]
    assert "CUS-000022" in target_customers
    assert "Opted Out" in findings[0]["actual_behavior"]


def test_detect_incorrect_return_deduction(setup_anomalies):
    """Verifies that Scenario 3 (Incorrect Return Calculation) is detected."""
    _, detector = setup_anomalies
    findings = detector.detect_incorrect_returns()
    assert len(findings) >= 1, "Failed to detect un-deducted product return"
    target_orders = [f["affected_record"] for f in findings]
    assert any("ORD-2026-ANOMALY-RET" in rec for rec in target_orders)


def test_detect_wrong_action_attribution(setup_anomalies):
    """Verifies that Scenario 4 (Wrong Action Attribution) is detected."""
    _, detector = setup_anomalies
    findings = detector.detect_wrong_attributions()
    assert len(findings) >= 1, "Failed to detect pre-dated action attribution"
    target_customers = [f["customer_id"] for f in findings]
    assert "CUS-000024" in target_customers


def test_benchmark_precision_and_recall_100_percent(setup_anomalies):
    """
    Verifies that the independent detector achieves 100% Precision and 100% Recall
    when benchmarked against ground truth.
    """
    _, detector = setup_anomalies
    eval_metrics = detector.evaluate_against_ground_truth()

    assert eval_metrics["precision"] == 1.0, f"Expected Precision 1.0, got {eval_metrics['precision']}"
    assert eval_metrics["recall"] == 1.0, f"Expected Recall 1.0, got {eval_metrics['recall']}"
    assert eval_metrics["f1_score"] == 1.0, f"Expected F1 1.0, got {eval_metrics['f1_score']}"
    assert eval_metrics["false_positives"] == 0, f"Found false positives: {eval_metrics['false_positives']}"
    assert eval_metrics["false_negatives"] == 0, f"Found false negatives: {eval_metrics['false_negatives']}"
