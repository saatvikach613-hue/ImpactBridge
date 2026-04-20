import psycopg2
import os
import sys

# The user confirmed password is 7613
PASSWORD = "7613"
HOSTS = ["localhost", "127.0.0.1", "::1"]
PORTS = [5432, 5433]
USERS = ["postgres", "chokkapusaatvika"]

working_string = None

print("Searching for your active Postgres connection...")

for port in PORTS:
    for host in HOSTS:
        for user in USERS:
            try:
                conn_str = f"postgresql://{user}:{PASSWORD}@{host}:{port}/impactbridge"
                conn = psycopg2.connect(conn_str)
                print(f"✅ FOUND IT: {conn_str}")
                working_string = conn_str
                conn.close()
                break
            except Exception:
                continue
        if working_string: break
    if working_string: break

if working_string:
    # Update .env
    env_path = "/Users/chokkapusaatvika/Downloads/ImpactBridge/.env"
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("DATABASE_URL="):
                f.write(f"DATABASE_URL={working_string}\n")
            else:
                f.write(line)
    
    print(f"Successfully updated {env_path}")
    sys.exit(0)
else:
    print("❌ Critical: Could not find active Postgres on 5432/5433 with user 'postgres' or 'chokkapusaatvika'.")
    sys.exit(1)
