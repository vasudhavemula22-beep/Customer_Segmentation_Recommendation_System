import sqlite3
import pytest
from pathlib import Path
from src.database.database import DatabaseManager

SCHEMA_PATH = Path("database") / "schema.sql"

REQUIRED_TABLES = {
    "customers",
    "products",
    "orders",
    "order_lines",
    "engagement_events",
    "support_cases",
    "consents",
    "segment_rules",
    "segment_memberships",
    "action_catalogs",
    "action_outcomes",
}

@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    temp_db_file = tmp_path / "test_crm.db"
    manager = DatabaseManager(db_path=temp_db_file)
    manager.initialize_schema(schema_path=SCHEMA_PATH)
    return manager

def test_all_11_tables_exist(test_db: DatabaseManager):
    tables = set(test_db.inspect_tables())
    missing_tables = REQUIRED_TABLES - tables
    assert len(missing_tables) == 0, f"Missing tables in database: {missing_tables}"
    assert len(tables) == 11, f"Expected 11 tables, found {len(tables)}"

def test_primary_key_uniqueness(test_db: DatabaseManager):
    with test_db.session() as conn:
        conn.execute(
            """
            INSERT INTO customers (
                customer_id, first_name, last_name, email, acquisition_channel, lifecycle_stage, created_at, updated_at
            ) VALUES (
                'CUS-000001', 'Alice', 'Smith', 'alice@example.com', 'Organic', 'Active', '2026-01-01 00:00:00', '2026-01-01 00:00:00'
            );
            """
        )
    with pytest.raises(sqlite3.IntegrityError):
        with test_db.session() as conn:
            conn.execute(
                """
                INSERT INTO customers (
                    customer_id, first_name, last_name, email, acquisition_channel, lifecycle_stage, created_at, updated_at
                ) VALUES (
                    'CUS-000001', 'Bob', 'Jones', 'bob@example.com', 'Direct', 'Active', '2026-01-02 00:00:00', '2026-01-02 00:00:00'
                );
                """
            )

def test_foreign_key_enforcement(test_db: DatabaseManager):
    with pytest.raises(sqlite3.IntegrityError):
        with test_db.session() as conn:
            conn.execute(
                """
                INSERT INTO orders (
                    order_id, customer_id, order_date, order_status, channel,
                    subtotal_amount, discount_amount, tax_amount, total_amount, net_amount, created_at
                ) VALUES (
                    'ORD-2026-000001', 'CUS-999999', '2026-01-01 10:00:00', 'Delivered', 'Web',
                    100.0, 0.0, 10.0, 110.0, 110.0, '2026-01-01 10:00:00'
                );
                """
            )

def test_check_constraint_enum(test_db: DatabaseManager):
    with pytest.raises(sqlite3.IntegrityError):
        with test_db.session() as conn:
            conn.execute(
                """
                INSERT INTO customers (
                    customer_id, first_name, last_name, email, acquisition_channel, lifecycle_stage, created_at, updated_at
                ) VALUES (
                    'CUS-000002', 'Charlie', 'Brown', 'charlie@example.com', 'INVALID_CHANNEL', 'Active', '2026-01-01 00:00:00', '2026-01-01 00:00:00'
                );
                """
            )

def test_check_constraint_negative_price(test_db: DatabaseManager):
    with pytest.raises(sqlite3.IntegrityError):
        with test_db.session() as conn:
            conn.execute(
                """
                INSERT INTO products (
                    product_id, product_name, category, base_price, cost, is_active, created_at
                ) VALUES (
                    'PRD-000001', 'Wireless Mouse', 'Electronics', -25.00, 10.00, 1, '2026-01-01 00:00:00'
                );
                """
            )

def test_cascade_delete_order_lines(test_db: DatabaseManager):
    with test_db.session() as conn:
        conn.execute(
            """
            INSERT INTO customers VALUES (
                'CUS-000010', 'David', 'Clark', 'david@example.com', NULL, 'Direct', 'Active', '2026-01-01 00:00:00', '2026-01-01 00:00:00'
            );
            """
        )
        conn.execute(
            """
            INSERT INTO products VALUES (
                'PRD-000010', 'Coffee Mug', 'Home & Kitchen', 15.00, 5.00, 1, '2026-01-01 00:00:00'
            );
            """
        )
        conn.execute(
            """
            INSERT INTO orders VALUES (
                'ORD-2026-000010', 'CUS-000010', '2026-01-05 12:00:00', 'Delivered', 'Web',
                15.00, 0.0, 1.50, 16.50, 16.50, '2026-01-05 12:00:00'
            );
            """
        )
        conn.execute(
            """
            INSERT INTO order_lines VALUES (
                'ORL-2026-000010', 'ORD-2026-000010', 'PRD-000010', 1, 15.00, 15.00, 0, 0.0, NULL, '2026-01-05 12:00:00'
            );
            """
        )
    
    count = test_db.execute_scalar("SELECT COUNT(*) FROM order_lines WHERE order_id = 'ORD-2026-000010';")
    assert count == 1

    test_db.execute_non_query("DELETE FROM orders WHERE order_id = 'ORD-2026-000010';")

    count_after = test_db.execute_scalar("SELECT COUNT(*) FROM order_lines WHERE order_id = 'ORD-2026-000010';")
    assert count_after == 0
