import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.database import engine
from app.models import Base
from app.api import auth, kids, sessions, dashboard, wishlist, ml
from app.api.automation import router as automation_router
from app.config import FRONTEND_URL, EXTRA_CORS_ORIGINS

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scheduler on startup, stop on shutdown."""
    Base.metadata.create_all(bind=engine)

    # Optional first-boot seed for hosted demos where there's no shell access
    # (e.g. Render free tier). Only runs when AUTO_SEED=true AND the users
    # table is empty, so it can never wipe real data.
    #
    # AUTO_SEED=force re-seeds even if data exists (drops all tables first).
    # Use it once to refresh the demo dataset, then set it back to "true".
    auto_seed = os.getenv("AUTO_SEED", "").lower()
    if auto_seed in ("1", "true", "yes", "force"):
        from app.database import SessionLocal
        from app.models import User
        db = SessionLocal()
        try:
            is_empty = db.query(User).count() == 0
        finally:
            db.close()
        if auto_seed == "force":
            print("[AUTO_SEED] force mode — dropping and re-seeding demo data...")
            from scripts.seed import run_seed
            run_seed()
            print("[AUTO_SEED] Done. Set AUTO_SEED back to 'true' to avoid re-seeding on every boot.")
        elif is_empty:
            print("[AUTO_SEED] Empty database detected — seeding demo data...")
            from scripts.seed import run_seed
            run_seed()
            print("[AUTO_SEED] Done.")
        else:
            print("[AUTO_SEED] Database already has data — skipping.")

    # Start the automation scheduler
    from app.automation.scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    yield  # server runs here

    stop_scheduler()


app = FastAPI(
    title="ImpactBridge API",
    description="""
Volunteer intelligence platform for U&I NGO.
Tracking kid progress, managing sessions, and powering fundraising
across chapters — with automated ML predictions every Sunday night.

Built from 9 months of direct field experience at U&I Visakhapatnam.
U&I: 62,484 volunteers | 2,00,508 lives impacted | 40 cities (2024-25)
    """,
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", FRONTEND_URL, *EXTRA_CORS_ORIGINS],
    # Also allow any Vercel preview deployment of this project
    allow_origin_regex=r"https://impact-?bridge[a-z0-9-]*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(kids.router)
app.include_router(sessions.router)
app.include_router(dashboard.router)
app.include_router(wishlist.router)
app.include_router(ml.router)
app.include_router(automation_router)


@app.get("/")
def root():
    return {
        "project":     "ImpactBridge",
        "description": "Volunteer intelligence platform for U&I NGO",
        "version":     "2.0.0",
        "docs":        "/docs",
        "u_and_i":     "62,484 volunteers | 2,00,508 lives impacted | 40 cities",
    }


@app.get("/health")
def health():
    return {"status": "ok", "scheduler": "running"}
