import psycopg2
import sys

connection_strings = [
    "postgresql://postgres:7613@localhost:5433/impactbridge",
    "postgresql://postgres:7613@localhost:5432/impactbridge",
    "postgresql://localhost:5433/impactbridge",
    "postgresql://localhost:5432/impactbridge",
    "postgresql:///impactbridge"
]

for conn_str in connection_strings:
    print(f"Testing: {conn_str}")
    try:
        conn = psycopg2.connect(conn_str)
        print("✅ SUCCESS!")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"❌ FAILED: {e}")

print("\nCould not connect to Postgres with any common settings.")
sys.exit(1)
