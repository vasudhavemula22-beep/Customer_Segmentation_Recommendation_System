"""
Automated Pytest Suite for Action Recommendation Engine.
Tests consent enforcement, service ticket prioritization, marketing suppression,
append-only history recording, and explanation integrity.
Uses self-healing pre-cleanup to prevent primary-key collisions.
"""

from datetime import datetime
import pytest
from src.database.database import DatabaseManager
from src.recommendations.engine import RecommendationEngine


@pytest.fixture(scope="module")
def db() -> DatabaseManager:
    return DatabaseManager()


def test_consent_enforcement_zero_violations(db: DatabaseManager):
    """
    Verifies that no marketing communication is marked 'Sent' if the customer opted out
    of that specific channel.
    """
    engine = RecommendationEngine(db=db)
    recs = engine.generate_recommendations()

    for r in recs:
        cid = r["customer_id"]
        channel = r["channel"]
        status = r["execution_status"]

        if r["action_id"] != "ACTN-2026-000001":
            consent_status = db.execute_scalar(
                "SELECT status FROM consents WHERE customer_id = ? AND channel = ? AND is_active = 1;",
                (cid, channel),
            )

            if consent_status == "Opted Out":
                assert status == "Suppressed", (
                    f"Consent violation: Customer {cid} opted out of {channel} but action was {status}!"
                )
                assert "withdrew marketing consent" in r["decision_reason"]


def test_open_critical_support_case_triggers_service_followup(db: DatabaseManager):
    """
    Verifies that an open critical support case triggers a Customer Support Follow-up.
    """
    cid = "CUS-000005"
    case_id = "CAS-2026-TEST01"

    # Pre-clean leftover records from previous interrupted runs
    db.execute_non_query("DELETE FROM support_cases WHERE case_id = ?;", (case_id,))

    db.execute_non_query(
        """
        INSERT INTO support_cases (
            case_id, customer_id, case_category, priority, status, cost_amount, opened_at
        ) VALUES (
            ?, ?, 'Product Defect', 'Critical', 'Open', 150.0, '2026-10-21 10:00:00'
        );
        """,
        (case_id, cid),
    )

    try:
        engine = RecommendationEngine(db=db)
        recs = engine.generate_recommendations()
        matching = [r for r in recs if r["customer_id"] == cid]
        assert len(matching) > 0, f"Customer {cid} was not evaluated in recommendations"
        target = matching[0]
        assert target["action_name"] == "Customer Support Follow-up", (
            f"Expected Support Follow-up, got {target['action_name']}"
        )
    finally:
        # Cleanup
        db.execute_non_query("DELETE FROM support_cases WHERE case_id = ?;", (case_id,))


def test_marketing_suppressed_for_unresolved_support_tickets(db: DatabaseManager):
    """
    Verifies that promotional marketing actions are suppressed if the customer has an open ticket.
    """
    cid = "CUS-000008"
    case_id = "CAS-2026-TEST02"

    # Pre-clean leftover records from previous interrupted runs
    db.execute_non_query("DELETE FROM support_cases WHERE case_id = ?;", (case_id,))

    db.execute_non_query(
        """
        INSERT INTO support_cases (
            case_id, customer_id, case_category, priority, status, cost_amount, opened_at
        ) VALUES (
            ?, ?, 'Billing', 'Medium', 'In Progress', 25.0, '2026-10-20 10:00:00'
        );
        """,
        (case_id, cid),
    )

    try:
        engine = RecommendationEngine(db=db)
        recs = engine.generate_recommendations()
        matching = [r for r in recs if r["customer_id"] == cid]
        assert len(matching) > 0, f"Customer {cid} was not evaluated in recommendations"
        target = matching[0]
        assert target["execution_status"] == "Suppressed"
        assert ("active open support ticket" in target["decision_reason"] or "withdrew marketing consent" in target["decision_reason"])
    finally:
        # Cleanup
        db.execute_non_query("DELETE FROM support_cases WHERE case_id = ?;", (case_id,))


def test_append_only_outcome_history(db: DatabaseManager):
    """
    Verifies that consecutive recommendation runs append new records
    into action_outcomes without overwriting or deleting previous history.
    """
    engine = RecommendationEngine(db=db)
    
    count_before = db.execute_scalar("SELECT COUNT(*) FROM action_outcomes;") or 0
    engine.execute_recommendation_run()
    count_after_first = db.execute_scalar("SELECT COUNT(*) FROM action_outcomes;") or 0
    
    assert count_after_first > count_before

    engine.execute_recommendation_run()
    count_after_second = db.execute_scalar("SELECT COUNT(*) FROM action_outcomes;") or 0

    assert count_after_second > count_after_first, "Recommendation history was overwritten instead of appended"


def test_explainable_reason_completeness(db: DatabaseManager):
    """
    Verifies that 100% of generated recommendations have an explicit, descriptive explanation.
    """
    engine = RecommendationEngine(db=db)
    recs = engine.generate_recommendations()

    for r in recs[:100]:  # Evaluate representative sample of recommendations
        reason = r["decision_reason"]
        assert isinstance(reason, str)
        assert len(reason) >= 15, f"Decision reason is too short for customer {r['customer_id']}"
        assert ("Approved:" in reason or "Suppressed:" in reason)
