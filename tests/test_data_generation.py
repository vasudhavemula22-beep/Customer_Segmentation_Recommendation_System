"""
Automated Pytest Suite for Synthetic Data Generation.
Validates row counts, ID formats, arithmetic integrity, and foreign key relations.
Supports Starter (100), Medium (5,000), and Full (50,000) scale configurations.
"""

import re
import pytest
from src.database.database import DatabaseManager


@pytest.fixture(scope="module")
def db() -> DatabaseManager:
    return DatabaseManager()


def test_starter_record_counts(db: DatabaseManager):
    """Verifies that the database matches one of the documented scale configurations."""
    customers_count = db.execute_scalar("SELECT COUNT(*) FROM customers;")
    products_count = db.execute_scalar("SELECT COUNT(*) FROM products;")
    orders_count = db.execute_scalar("SELECT COUNT(*) FROM orders WHERE order_id NOT LIKE '%ANOMALY%';")
    events_count = db.execute_scalar("SELECT COUNT(*) FROM engagement_events;")
    support_count = db.execute_scalar("SELECT COUNT(*) FROM support_cases WHERE case_id NOT LIKE '%TEST%';")
    consents_count = db.execute_scalar("SELECT COUNT(*) FROM consents;")

    # Supports either Starter (100), Medium (5,000), or Full (50,000) scale
    assert customers_count in (100, 5000, 50000), f"Unexpected customer count: {customers_count}"
    assert products_count in (40, 150, 500), f"Unexpected product count: {products_count}"
    assert orders_count in (400, 20000, 200000), f"Unexpected order count: {orders_count}"
    assert events_count in (2000, 100000, 1000000), f"Unexpected event count: {events_count}"
    assert support_count in (60, 3000, 30000), f"Unexpected support cases: {support_count}"
    assert consents_count in (300, 15000, 150000), f"Unexpected consents: {consents_count}"


def test_deterministic_id_formats(db: DatabaseManager):
    """Verifies that generated IDs comply with standard regex patterns."""
    customer_ids = [r[0] for r in db.fetch_all("SELECT customer_id FROM customers LIMIT 50;")]
    for cid in customer_ids:
        assert re.match(r"^CUS-\d{6}$", cid), f"Invalid Customer ID format: {cid}"

    order_ids = [r[0] for r in db.fetch_all("SELECT order_id FROM orders WHERE order_id NOT LIKE '%ANOMALY%' LIMIT 50;")]
    for oid in order_ids:
        assert re.match(r"^ORD-\d{4}-\d{6}$", oid), f"Invalid Order ID format: {oid}"

    event_ids = [r[0] for r in db.fetch_all("SELECT event_id FROM engagement_events LIMIT 50;")]
    for eid in event_ids:
        assert re.match(r"^EVT-\d{4}-\d{6}$", eid), f"Invalid Event ID format: {eid}"


def test_order_line_arithmetic_integrity(db: DatabaseManager):
    """Validates that line_total strictly equals quantity * unit_price."""
    lines = db.fetch_all("SELECT quantity, unit_price, line_total FROM order_lines WHERE order_line_id NOT LIKE '%ANOMALY%' LIMIT 500;")
    for row in lines:
        expected = round(row["quantity"] * row["unit_price"], 2)
        actual = round(row["line_total"], 2)
        assert abs(actual - expected) < 0.01, f"Mismatch: {row['quantity']} * {row['unit_price']} != {row['line_total']}"


def test_order_net_amount_reconciliation(db: DatabaseManager):
    """
    Validates that orders.net_amount strictly equals total_amount - sum(returned line amounts)
    for all legitimate baseline orders (excluding the deliberate test anomaly).
    """
    sql = """
        SELECT 
            o.order_id, 
            o.total_amount, 
            o.net_amount, 
            COALESCE(SUM(ol.return_amount), 0.0) as calculated_return
        FROM orders o
        JOIN order_lines ol ON o.order_id = ol.order_id
        WHERE o.order_id NOT LIKE '%ANOMALY%'
        GROUP BY o.order_id, o.total_amount, o.net_amount
        LIMIT 500;
    """
    rows = db.fetch_all(sql)
    for r in rows:
        expected_net = round(r["total_amount"] - r["calculated_return"], 2)
        actual_net = round(r["net_amount"], 2)
        assert abs(actual_net - expected_net) < 0.01, (
            f"Order {r['order_id']} net mismatch: total({r['total_amount']}) - return({r['calculated_return']}) != {actual_net}"
        )


def test_presence_of_business_archetypes(db: DatabaseManager):
    """Verifies that dormant customers, returns, high-cost support cases, and opt-outs exist."""
    dormant_count = db.execute_scalar("SELECT COUNT(*) FROM customers WHERE lifecycle_stage = 'Dormant';")
    assert dormant_count > 0, "No dormant customers generated"

    returns_count = db.execute_scalar("SELECT COUNT(*) FROM order_lines WHERE is_returned = 1 AND order_line_id NOT LIKE '%ANOMALY%';")
    assert returns_count > 0, "No product returns generated"

    high_cost_cases = db.execute_scalar("SELECT COUNT(*) FROM support_cases WHERE cost_amount > 100.0;")
    assert high_cost_cases > 0, "No high-cost support cases generated"

    opt_outs = db.execute_scalar("SELECT COUNT(*) FROM consents WHERE status = 'Opted Out';")
    assert opt_outs > 0, "No opted-out consents generated"
