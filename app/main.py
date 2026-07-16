from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import get_db
from app.routers import resume, match, tracker, dashboard, loot

app = FastAPI(
    title="Zeno API",
    description="Backend for Zeno AI Career Super-App",
    version="1.0.0"
)

# CORS — allow Android app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(match.router)
app.include_router(tracker.router)
app.include_router(dashboard.router)
app.include_router(loot.router)

@app.get("/")
def read_root():
    return {"message": "Zeno API v1.0 — AI Career Super-App Backend", "status": "running"}

@app.get("/ping")
def ping():
    """Keep-alive endpoint — pinged every 10 min by cron-job.org to prevent Render spin-down."""
    return {"status": "awake", "message": "Zeno backend is alive! 🚀"}

@app.get("/health")
def health_check():
    db = get_db()
    db_status = "connected" if db else "disconnected"
    return {"status": "healthy", "database": db_status}
