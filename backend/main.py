from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .database import engine, Base
from .routers import auth, admin, onboarding, dashboard

# Create database tables
Base.metadata.create_all(bind=engine)

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
    os.makedirs("uploads", exist_ok=True)
except Exception as e:
    print(f"Directory creation skipped (read-only file system): {e}")

app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

@app.get("/review/{user_id}")
def read_public_review(user_id: int):
    return FileResponse("frontend/public_review.html")
