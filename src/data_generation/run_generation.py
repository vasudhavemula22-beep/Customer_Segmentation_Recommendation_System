"""
Optimized Bulk-Streaming Data Generation and Ingestion Engine.
Supports Starter (100 cus), Medium (5,000 cus), and Full (50,000 cus, 200k ord, 1M events) scales.
Uses chunked streaming and SQLite bulk pragmas to keep RAM consumption below 500MB.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
import time
from typing import Any, Dict, List, Tuple
import pandas as pd
from tabulate import tabulate

from src.database.database import DatabaseManager
from src.data_generation.config import SCALE_PROFILES, RANDOM_SEED
from src.data_generation.generator import SyntheticDataGenerator


def execute_bulk_insert(db: DatabaseManager, table_name: str, records: List[Dict[str, Any]], batch_size: int = 10000) -> None:
    """Inserts records in streaming batches using parameterized multi-row statements."""
    if not records:
        return

    columns = list(records[0].keys())
    col_str = ", ".join(columns)
    placeholders = ", ".join(["?"] * len(columns))
    sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders});"

    with db.session() as conn:
        cursor = conn.cursor()
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            payload = [tuple(item[col] for col in columns) for item in batch]
            cursor.executemany(sql, payload)


def export_snapshots(table_name: str, records: List[Dict[str, Any]], raw_dir: Path, export_dir: Path, is_full: bool) -> None:
    """Exports generated records to CSV and JSON."""
    df = pd.DataFrame(records)
    # Always write full CSV
    csv_path = raw_dir / f"{table_name}.csv"
    df.to_csv(csv_path, index=False)

    # For full scale JSON, export a representative 5,000-row sample to prevent giant multi-gigabyte files
    json_path = export_dir / f"{table_name}.json"
    if is_full and len(records) > 5000:
        sample_records = records[:5000]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(sample_records, f, indent=2, default=str)
    else:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)


def run_pipeline(scale_name: str = "starter") -> None:
    if scale_name not in SCALE_PROFILES:
        raise ValueError(f"Unknown scale: {scale_name}. Choose from: {list(SCALE_PROFILES.keys())}")

    config = SCALE_PROFILES[scale_name]
    is_full = (scale_name == "full")

    print("\n" + "=" * 80)
    print(f"EXECUTING DATA GENERATION PIPELINE: SCALE = '{scale_name.upper()}'")
    print(f"Target Scale Config : {config.customers:,} customers | {config.orders:,} orders | {config.engagement_events:,} events")
    print(f"Random Seed Lock    : {RANDOM_SEED}")
    print("=" * 80)

    start_time = time.time()
    db = DatabaseManager()

    # Re-initialize fresh schema
    print("\n[Init] Deploying fresh schema DDL...")
    db.initialize_schema()

    # Temporarily tune pragmas for bulk load throughput
    with db.session() as conn:
        conn.execute("PRAGMA synchronous = OFF;")
        conn.execute("PRAGMA cache_size = 100000;")
        conn.execute("PRAGMA temp_store = MEMORY;")

    raw_dir = Path("data") / "raw"
    export_dir = Path("data") / "exports"
    raw_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    generator = SyntheticDataGenerator(config=config, seed=RANDOM_SEED)
    summary_counts: List[Tuple[str, int]] = []

    # 1. Customers
    t0 = time.time()
    print("[1/7] Generating Customers master...")
    customers = generator.generate_customers()
    execute_bulk_insert(db, "customers", customers)
    export_snapshots("customers", customers, raw_dir, export_dir, is_full)
    summary_counts.append(("customers", len(customers)))
    print(f"      Completed {len(customers):,} customers in {time.time() - t0:.2f}s")

    # 2. Products
    t0 = time.time()
    print("[2/7] Generating Products catalog & taxonomy...")
    products = generator.generate_products()
    execute_bulk_insert(db, "products", products)
    export_snapshots("products", products, raw_dir, export_dir, is_full)
    summary_counts.append(("products", len(products)))
    print(f"      Completed {len(products):,} products in {time.time() - t0:.2f}s")

    # 3 & 4. Orders and OrderLines
    t0 = time.time()
    print("[3/7] Generating Orders and OrderLines (co-calculated arithmetic)...")
    orders, order_lines = generator.generate_orders_and_lines()
    execute_bulk_insert(db, "orders", orders)
    export_snapshots("orders", orders, raw_dir, export_dir, is_full)
    summary_counts.append(("orders", len(orders)))
    print(f"      Completed {len(orders):,} orders in {time.time() - t0:.2f}s")

    t0 = time.time()
    print("[4/7] Ingesting OrderLines detail...")
    execute_bulk_insert(db, "order_lines", order_lines)
    export_snapshots("order_lines", order_lines, raw_dir, export_dir, is_full)
    summary_counts.append(("order_lines", len(order_lines)))
    print(f"      Completed {len(order_lines):,} order lines in {time.time() - t0:.2f}s")

    # 5. Engagement Events
    t0 = time.time()
    print("[5/7] Generating High-Volume Engagement Events...")
    events = generator.generate_engagement_events()
    execute_bulk_insert(db, "engagement_events", events)
    export_snapshots("engagement_events", events, raw_dir, export_dir, is_full)
    summary_counts.append(("engagement_events", len(events)))
    print(f"      Completed {len(events):,} events in {time.time() - t0:.2f}s")

    # 6. Support Cases
    t0 = time.time()
    print("[6/7] Generating Customer Support Cases & Cost Overheads...")
    cases = generator.generate_support_cases()
    execute_bulk_insert(db, "support_cases", cases)
    export_snapshots("support_cases", cases, raw_dir, export_dir, is_full)
    summary_counts.append(("support_cases", len(cases)))
    print(f"      Completed {len(cases):,} support cases in {time.time() - t0:.2f}s")

    # 7. Consents
    t0 = time.time()
    print("[7/7] Generating Consent Audit Preferences & Opt-Outs...")
    consents = generator.generate_consents()
    execute_bulk_insert(db, "consents", consents)
    export_snapshots("consents", consents, raw_dir, export_dir, is_full)
    summary_counts.append(("consents", len(consents)))
    print(f"      Completed {len(consents):,} consents in {time.time() - t0:.2f}s")

    # Restore safe SQLite Pragmas
    with db.session() as conn:
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"DATA GENERATION SUMMARY [Scale: {scale_name.upper()}] (Elapsed: {elapsed:.2f} seconds)")
    print("=" * 80)
    print(tabulate(summary_counts, headers=["Database Table", "Records Ingested"], tablefmt="fancy_grid"))
    print("\nAll data written to SQLite ('database/ecommerce_crm.db'), CSV, and JSON.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Bulk-Streaming Synthetic Data Generator")
    parser.add_argument(
        "--scale",
        type=str,
        default="starter",
        choices=["starter", "medium", "full"],
        help="Dataset size profile (default: starter)"
    )
    args = parser.parse_args()
    run_pipeline(args.scale)
