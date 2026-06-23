"""
Supabase PostgreSQL Migration Script
Connects to the Supabase database and creates all tables defined in the SQLAlchemy models.
"""
import os
import sys

# Set UTF-8 output for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Force the DATABASE_URL to Supabase before importing backend modules
# Note: @ in password must be encoded as %40 in the URL
SUPABASE_URL = "postgresql://postgres:Joliya%40283283@db.sgushsxnhnipqewomuby.supabase.co:5432/postgres"
os.environ["DATABASE_URL"] = SUPABASE_URL

# Add the project root to sys.path so backend imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("[*] Connecting to Supabase PostgreSQL...")
print("    Host: db.sgushsxnhnipqewomuby.supabase.co:5432")

try:
    from sqlalchemy import create_engine, text

    engine = create_engine(SUPABASE_URL)

    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        row = result.fetchone()
        print(f"[OK] Connected! PostgreSQL version: {row[0][:60]}...")

    print("\n[*] Creating all tables from SQLAlchemy models...")
    from backend.models import Base
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created successfully!\n")

    # List all created tables
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        print("[*] Tables in Supabase database:")
        for t in tables:
            print(f"    - {t}")

    print("\n[DONE] Migration complete! Your Supabase database is ready.")
    print("       Next: Add DATABASE_URL to Vercel Environment Variables")

except Exception as e:
    print(f"\n[ERROR] Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
