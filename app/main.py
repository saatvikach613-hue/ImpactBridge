from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.database import engine
from app.models import Base
from app.api import auth, kids, sessions, dashboard, wishlist, ml
from app.api.automation import router as automation_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scheduler on startup, stop on shutdown."""
    Base.metadata.create_all(bind=engine)

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
    allow_origins=["http://localhost:3000", "https://impactbridge.vercel.app"],
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
