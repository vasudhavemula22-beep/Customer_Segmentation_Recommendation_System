"""
Verification Script for Phase 1 Setup.
Tests Python environment, standard libraries, installed third-party libraries,
and SQLite in-memory operations on the D: drive.
"""
import sys
import sqlite3
from datetime import datetime

def run_verification() -> bool:
    print("=" * 60)
    print("SYSTEM ENVIRONMENT VERIFICATION")
    print("=" * 60)
    print(f"Timestamp        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version   : {sys.version.split()[0]}")
    
    # 1. Verify Virtual Environment
    is_venv = sys.prefix != sys.base_prefix
    print(f"In Virtual Env   : {'YES (Correct)' if is_venv else 'NO (Error - Activate .venv)'}")
    if not is_venv:
        return False

    # 2. Verify Core Packages
    packages = [
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("streamlit", "Streamlit"),
        ("plotly", "Plotly"),
        ("pytest", "Pytest"),
        ("dateutil", "Python-Dateutil"),
        ("tabulate", "Tabulate"),
    ]

    print("\n--- Verifying Installed Packages ---")
    all_packages_ok = True
    for module_name, display_name in packages:
        try:
            mod = __import__(module_name)
            version = getattr(mod, "__version__", "Available")
            print(f"[PASS] {display_name:<18}: Version {version}")
        except ImportError as e:
            print(f"[FAIL] {display_name:<18}: NOT INSTALLED ({e})")
            all_packages_ok = False

    # 3. Verify SQLite Driver
    print("\n--- Verifying SQLite Driver & In-Memory Operations ---")
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE phase1_test (id INTEGER PRIMARY KEY, status TEXT);")
        cursor.execute("INSERT INTO phase1_test (status) VALUES ('verified');")
        conn.commit()
        cursor.execute("SELECT status FROM phase1_test WHERE id = 1;")
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] == "verified":
            print(f"[PASS] SQLite Engine       : Operational (SQLite {sqlite3.sqlite_version})")
            sqlite_ok = True
        else:
            print("[FAIL] SQLite Engine       : Unexpected test query result")
            sqlite_ok = False
    except Exception as e:
        print(f"[FAIL] SQLite Engine       : Error ({e})")
        sqlite_ok = False

    print("=" * 60)
    if all_packages_ok and sqlite_ok and is_venv:
        print("ALL CHECKS PASSED: Environment is ready for Phase 2.")
        print("=" * 60)
        return True
    else:
        print("VERIFICATION FAILED: Please fix the errors listed above.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
