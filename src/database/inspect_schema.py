"""
Database Schema Inspector Tool.
Prints tabular schema definitions, data types, primary keys, and foreign keys.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tabulate import tabulate
from src.database.database import DatabaseManager


def print_schema_summary() -> None:
    db = DatabaseManager()
    tables = db.inspect_tables()

    print("\n" + "=" * 80)
    print("DATABASE SCHEMA OVERVIEW: ecommerce_crm.db")
    print("=" * 80)
    print(f"Total Managed Tables: {len(tables)}\n")

    for table in tables:
        print(f"TABLE: {table.upper()}")
        print("-" * 60)

        # Columns
        cols = db.inspect_columns(table)
        col_headers = ["Col #", "Name", "Type", "NotNull", "Default", "PK"]
        col_rows = [
            [c["column_id"], c["name"], c["data_type"], c["not_null"], c["default_value"], c["primary_key"]]
            for c in cols
        ]
        print(tabulate(col_rows, headers=col_headers, tablefmt="simple"))

        # Foreign Keys
        fks = db.inspect_foreign_keys(table)
        if fks:
            print("\nForeign Keys:")
            fk_headers = ["From Column", "Target Table", "Target Column", "On Delete"]
            fk_rows = [
                [fk["from_column"], fk["to_table"], fk["to_column"], fk["on_delete"]]
                for fk in fks
            ]
            print(tabulate(fk_rows, headers=fk_headers, tablefmt="simple"))
        else:
            print("\nForeign Keys: None (Root Entity)")

        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    print_schema_summary()
