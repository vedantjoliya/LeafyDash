import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# Fallback for Vercel serverless (read-only filesystem)
if os.getenv("VERCEL") and DATABASE_URL == "sqlite:///./database.db":
    DATABASE_URL = "sqlite:////tmp/database.db"

# Normalise Heroku/Render postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; PostgreSQL does not
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Pool settings for PostgreSQL on Vercel serverless (short-lived lambdas)
engine_kwargs = dict(connect_args=connect_args)
if DATABASE_URL.startswith("postgresql"):
    engine_kwargs.update(
        pool_pre_ping=True,    # verify connection is alive before use
        pool_recycle=300,      # recycle connections every 5 min
        pool_size=5,
        max_overflow=10,
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
