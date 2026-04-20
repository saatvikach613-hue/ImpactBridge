import psycopg2
import sys
import os

usernames = ["postgres", "chokkapusaatvika", os.getlogin()]
passwords = ["7613", ""]
ports = [5432, 5433]

for port in ports:
    for user in usernames:
        for password in passwords:
            conn_str = f"postgresql://{user}:{password}@localhost:{port}/impactbridge"
            print(f"Testing: {conn_str}")
            try:
                conn = psycopg2.connect(conn_str)
                print("✅ SUCCESS!")
                conn.close()
                sys.exit(0)
            except Exception as e:
                # print(f"❌ FAILED: {e}")
                pass

print("\nAll permutations failed.")
sys.exit(1)
