import psycopg2
import sys

# The user confirmed password is 7613
PASSWORD = "7613"
HOSTS = ["127.0.0.1", "localhost"]
PORTS = [5432, 5433, 5434] # Added one more common fallback
USERS = ["postgres", "chokkapusaatvika"]
DBs = ["postgres", "template1"] # Connect to system DBs first

working_conn = None

for port in PORTS:
    for host in HOSTS:
        for user in USERS:
            for db in DBs:
                try:
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        user=user,
                        password=PASSWORD,
                        dbname=db
                    )
                    print(f"✅ SERVER CONNECTED: host={host}, port={port}, user={user}, db={db}")
                    working_conn = (host, port, user, db)
                    conn.close()
                    break
                except Exception:
                    continue
            if working_conn: break
        if working_conn: break
    if working_conn: break

if working_conn:
    print(f"RESULT: {working_conn}")
    sys.exit(0)
else:
    print("❌ Total failure: Still no server access.")
    sys.exit(1)
