import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# In serverless environments like Vercel, relative paths for SQLite databases
# fail because the filesystem is read-only. We rewrite relative sqlite paths to use /tmp.
if os.getenv("VERCEL") and DATABASE_URL.startswith("sqlite:///."):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///.", "sqlite:////tmp", 1)

# For PostgreSQL URL from Heroku/Render etc., convert postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_SQLITE = DATABASE_URL.startswith("sqlite")
IS_SERVERLESS = os.getenv("VERCEL") is not None

if IS_SQLITE:
    # SQLite: needs check_same_thread=False, no pool config
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
elif IS_SERVERLESS:
    # Vercel serverless: NullPool prevents connection re-use between lambda invocations.
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"connect_timeout": 10},
    )
else:
    # Local / persistent server: use a normal connection pool
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 10},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
