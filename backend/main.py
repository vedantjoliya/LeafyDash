from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
import traceback

from .database import engine, Base
from .routers import auth, admin, onboarding, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: create all database tables (wrapped so a bad DB URL doesn't
    crash the entire Vercel lambda at import time).
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created / verified OK")
    except Exception as exc:
        # Log the error but let the app start – API health check will surface it
        print(f"WARNING: Could not run create_all: {exc}")
    yield
    # Shutdown logic here if needed


app = FastAPI(
    title="Leafy Dash",
    description="A secure modular business dashboard system customized for your operational needs.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(onboarding.router)
app.include_router(dashboard.router)

# ── Global exception handler (surfaces real errors for debugging) ─────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}", "traceback": tb},
    )

# ── Static file directories ───────────────────────────────────────────────────
upload_dir = "/tmp/uploads" if os.getenv("VERCEL") else "uploads"

for d in ["frontend/css", "frontend/js", "frontend/images", upload_dir]:
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass

for _route, _dir, _name in [
    ("/css",     "frontend/css",    "css"),
    ("/js",      "frontend/js",     "js"),
    ("/images",  "frontend/images", "images"),
    ("/uploads", upload_dir,        "uploads"),
]:
    try:
        if os.path.isdir(_dir):
            app.mount(_route, StaticFiles(directory=_dir), name=_name)
    except Exception as e:
        print(f"Static mount skipped for {_dir}: {e}")

# ── Frontend HTML routes ──────────────────────────────────────────────────────
@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")

@app.get("/login")
def read_login():
    return FileResponse("frontend/login.html")

@app.get("/register")
def read_register():
    return FileResponse("frontend/register.html")

@app.get("/admin-portal")
def read_admin():
    return FileResponse("frontend/admin.html")

@app.get("/onboarding")
def read_onboarding():
    return FileResponse("frontend/onboarding.html")

@app.get("/dashboard")
def read_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.get("/promo")
def read_promo():
    return FileResponse("frontend/promo.html")

@app.get("/review/{user_id}")
def read_public_review(user_id: int):
    return FileResponse("frontend/public_review.html")

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    from .database import DATABASE_URL
    db_type = "postgresql" if "postgresql" in DATABASE_URL else "sqlite"
    return {"status": "ok", "db": db_type}
