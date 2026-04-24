from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.database import engine, Base
from app.routers import auth, apikey, logistics, billing, profile, telegram_bot

# Initialize Database
# Note: In production, use Alembic. For UTS, this is convenient.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Logistics Rate & Tracking API",
    description="API for checking shipping rates and tracking packages (UTS Semester 6)",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(apikey.router)
app.include_router(logistics.router)
app.include_router(billing.router)
app.include_router(profile.router)
app.include_router(telegram_bot.router, prefix="/api/v1")

# Mount static files (frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    # Mount assets folder specifically at /assets to match HTML links href="assets/..."
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")
    # Also keep /static as a backup
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")

@app.get("/api/")
def api_root():
    return {
        "message": "Welcome to Logistics API",
        "author": "Yogi Prasetyo",
        "nim": "22081010297",
        "docs": "/docs"
    }

@app.get("/")
async def frontend_index():
    return FileResponse(
        str(frontend_path / "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/dashboard")
async def frontend_dashboard():
    # Serve the actual dashboard.html with fixes and disable caching
    return FileResponse(
        str(frontend_path / "dashboard.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/index.html")
async def frontend_index_html():
    return FileResponse(
        str(frontend_path / "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/dashboard.html")
async def frontend_dashboard_html():
    return FileResponse(
        str(frontend_path / "dashboard.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
