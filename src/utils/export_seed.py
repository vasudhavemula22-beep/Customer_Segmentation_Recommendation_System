"""
SQL Seed Data Exporter for Public GitHub Repository.
Dumps clean, portable seed data for all 11 tables into database/seed_data.sql.
Guaranteed to stay under GitHub's 100MB file size limit.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import DatabaseManager


def export_clean_seed() -> None:
    db = DatabaseManager()
    output_path = Path("database") / "seed_data.sql"
    tables = db.inspect_tables()

    print(f"Exporting clean repository SQL seed data to: {output_path.resolve()}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- =============================================================================\n")
        f.write("-- EXPLAINABLE CRM INTELLIGENCE SYSTEM - SEED DATA\n")
        f.write("-- =============================================================================\n\n")
        f.write("PRAGMA foreign_keys = OFF;\nBEGIN TRANSACTION;\n\n")

        for table in tables:
            # Export all rows for taxonomy tables; sample first 200 rows for high-volume event/order tables
            limit_clause = "" if table in ("segment_rules", "action_catalogs", "products") else "LIMIT 200"
            rows = db.fetch_all(f"SELECT * FROM {table} {limit_clause};")
            if not rows:
                continue

            columns = list(rows[0].keys())
            col_names = ", ".join(columns)
            f.write(f"-- Table: {table} ({len(rows)} seed records)\n")

            for r in rows:
                values = []
                for col in columns:
                    val = r[col]
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        clean_str = str(val).replace("'", "''")
                        values.append(f"'{clean_str}'")
                f.write(f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({', '.join(values)});\n")
            f.write("\n")

        f.write("COMMIT;\nPRAGMA foreign_keys = ON;\n")

    size_kb = output_path.stat().st_size / 1024
    print(f"Successfully generated clean seed file: {output_path.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    export_clean_seed()
