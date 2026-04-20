import psycopg2
import sys
import os

PASSWORDS = ["7613", "7777"]
PORTS = [5432, 5433, 5434]
HOSTS = ["localhost", "127.0.0.1", "::1"]
USERS = ["postgres", "chokkapusaatvika"]

print("🚀 Starting ULTIMATE PROBE...")

working_str = None

for port in PORTS:
    for host in HOSTS:
        for password in PASSWORDS:
            for user in USERS:
                try:
                    conn_str = f"postgresql://{user}:{password}@{host}:{port}/impactbridge"
                    # Try connecting to the specific DB
                    conn = psycopg2.connect(conn_str, connect_timeout=2)
                    print(f"✅ SUCCESS: {conn_str}")
                    working_str = conn_str
                    conn.close()
                    break
                except Exception:
                    # Try connecting to system DB just to see if the server exists
                    try:
                        sys_conn_str = f"postgresql://{user}:{password}@{host}:{port}/postgres"
                        conn = psycopg2.connect(sys_conn_str, connect_timeout=2)
                        print(f"⚠️  SERVER FOUND but 'impactbridge' DB missing: {sys_conn_str}")
                        working_str = sys_conn_str # Point to postgres DB for now
                        conn.close()
                        break
                    except Exception:
                        continue
            if working_str: break
        if working_str: break
    if working_str: break

if working_str:
    # Update .env
    env_path = "/Users/chokkapusaatvika/Downloads/ImpactBridge/.env"
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("DATABASE_URL="):
                f.write(f"DATABASE_URL={working_str}\n")
            else:
                f.write(line)
    
    print(f"\n✨ UPDATED .env: {working_str}")
    sys.exit(0)
else:
    print("\n❌ All combinations failed. Please check if Postgres.app is actually running and showing a green dot.")
    sys.exit(1)
