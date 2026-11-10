from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple
from contextlib import contextmanager
import pandas as pd

class DatabaseManager:
    DEFAULT_DB_PATH = Path("database") / "ecommerce_crm.db"
    DEFAULT_SCHEMA_PATH = Path("database") / "schema.sql"

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self._ensure_parent_directory()

    def _ensure_parent_directory(self) -> None:
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    @contextmanager
    def session(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self, schema_path: Optional[str | Path] = None) -> None:
        sql_file = Path(schema_path) if schema_path else self.DEFAULT_SCHEMA_PATH
        if not sql_file.exists():
            raise FileNotFoundError(f"Schema file not found at: {sql_file.resolve()}")

        with open(sql_file, "r", encoding="utf-8") as f:
            ddl_script = f.read()

        with self.session() as conn:
            conn.executescript(ddl_script)

    def execute_non_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> int:
        with self.session() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.rowcount

    def execute_scalar(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Any:
        with self.session() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            row = cursor.fetchone()
            return row[0] if row else None

    def fetch_all(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[sqlite3.Row]:
        with self.session() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()

    def fetch_dataframe(self, sql: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        with self.session() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def inspect_tables(self) -> List[str]:
        sql = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [row["name"] for row in cursor.fetchall()]

    def inspect_columns(self, table_name: str) -> List[dict[str, Any]]:
        sql = f"PRAGMA table_info({table_name});"
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "column_id": row["cid"],
                    "name": row["name"],
                    "data_type": row["type"],
                    "not_null": bool(row["notnull"]),
                    "default_value": row["dflt_value"],
                    "primary_key": bool(row["pk"])
                })
            return columns

    def inspect_foreign_keys(self, table_name: str) -> List[dict[str, Any]]:
        sql = f"PRAGMA foreign_key_list({table_name});"
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            fks = []
            for row in cursor.fetchall():
                fks.append({
                    "id": row["id"],
                    "from_column": row["from"],
                    "to_table": row["table"],
                    "to_column": row["to"],
                    "on_update": row["on_update"],
                    "on_delete": row["on_delete"]
                })
            return fks

if __name__ == "__main__":
    db = DatabaseManager()
    print(f"Initializing database at: {db.db_path.resolve()}")
    db.initialize_schema()
    tables = db.inspect_tables()
    print(f"Successfully initialized {len(tables)} tables:")
    for t in tables:
        print(f"  - {t}")
