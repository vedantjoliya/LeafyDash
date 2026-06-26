from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .database import engine, Base
from .routers import auth, admin, onboarding, dashboard

# Create database tables with startup resilience
db_init_error = None
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    import traceback
    db_init_error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    print(f"CRITICAL DATABASE INITIALIZATION ERROR: {db_init_error}")

app = FastAPI(
    title="Leafy Dash",
    description="A secure modular business dashboard system customized for your operational needs.",
    version="1.0.0"
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache control middleware to prevent stale cache on browser
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    # Disable cache for API endpoints and direct HTML routes
    if path.startswith("/api") or path.endswith(".html") or path in ["/", "/login", "/register", "/admin-portal", "/onboarding", "/dashboard", "/promo"]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# Include API routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(onboarding.router)
app.include_router(dashboard.router)

# Mount Static Directories for CSS/JS assets if they exist
try:
    os.makedirs("frontend/css", exist_ok=True)
    os.makedirs("frontend/js", exist_ok=True)
    os.makedirs("frontend/images", exist_ok=True)
except Exception as e:
    print(f"Static directory creation skipped: {e}")

uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    try:
        os.makedirs(uploads_dir, exist_ok=True)
    except Exception as e:
        print(f"Uploads directory creation failed (read-only file system), falling back to /tmp: {e}")
        uploads_dir = "/tmp/uploads"
        os.makedirs(uploads_dir, exist_ok=True)

app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Frontend Page Routes (Serving HTML files securely)
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

# ── Debug endpoint (safe — no secrets exposed) ────────────────────────────────
@app.get("/api/debug")
def debug():
    import os
    from .auth import ADMIN_USERNAME
    from .database import DATABASE_URL
    return {
        "DATABASE_URL_scheme": DATABASE_URL.split("://")[0] if "://" in DATABASE_URL else "unknown",
        "DATABASE_URL_host": DATABASE_URL.split("@")[-1].split(":")[0].split("/")[0] if "@" in DATABASE_URL else "local/sqlite",
        "DATABASE_URL_port": DATABASE_URL.split("@")[-1].split(":")[1].split("/")[0] if "@" in DATABASE_URL and ":" in DATABASE_URL.split("@")[-1] else "default",
        "JWT_SECRET_KEY_set": os.getenv("JWT_SECRET_KEY") is not None,
        "JWT_SECRET_KEY_is_default": os.getenv("JWT_SECRET_KEY") == "antigravity_super_secret_session_key_987654321",
        "ADMIN_USERNAME": ADMIN_USERNAME,
        "ADMIN_PASSWORD_set": os.getenv("ADMIN_PASSWORD") is not None,
        "running_on_vercel": os.getenv("VERCEL") is not None,
        "db_init_error": db_init_error
    }
