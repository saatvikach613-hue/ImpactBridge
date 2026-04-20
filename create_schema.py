from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("No database url")
    exit(1)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    conn.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
    print("Analytics schema created.")
