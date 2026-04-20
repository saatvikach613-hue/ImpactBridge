import psycopg2
import sys
import os

socket_paths = [
    "/tmp",
    "/var/run/postgresql",
    "/Library/PostgreSQL/18/data"
]
usernames = ["postgres", "chokkapusaatvika"]
passwords = ["7613", ""]

for path in socket_paths:
    if os.path.exists(path):
        for user in usernames:
            for password in passwords:
                try:
                    # In psycopg2, host starting with / means unix socket directory
                    conn = psycopg2.connect(
                        host=path,
                        user=user,
                        password=password,
                        dbname="impactbridge",
                        port=5432
                    )
                    print(f"✅ SUCCESS on socket {path} (user={user})")
                    conn.close()
                    sys.exit(0)
                except Exception as e:
                    # print(f"❌ Socket {path} (user={user}) failed: {e}")
                    pass

print("\nSocket connection failed. Testing TCP one last time on standard ports...")
# ... already tested TCP ...
sys.exit(1)
