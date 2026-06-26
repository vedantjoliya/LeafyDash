import sqlite3
import os

db_path = "database.db"

if not os.path.exists(db_path):
    print("Database file not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Add start_date
try:
    print("Adding start_date column to marketing_campaigns...")
    cursor.execute("ALTER TABLE marketing_campaigns ADD COLUMN start_date DATETIME;")
    print("Added start_date column.")
except Exception as e:
    print(f"start_date already exists or error: {e}")

# 2. Add end_date
try:
    print("Adding end_date column to marketing_campaigns...")
    cursor.execute("ALTER TABLE marketing_campaigns ADD COLUMN end_date DATETIME;")
    print("Added end_date column.")
except Exception as e:
    print(f"end_date already exists or error: {e}")

# 3. Add status
try:
    print("Adding status column to marketing_campaigns...")
    cursor.execute("ALTER TABLE marketing_campaigns ADD COLUMN status TEXT DEFAULT 'active';")
    print("Added status column.")
except Exception as e:
    print(f"status already exists or error: {e}")

conn.commit()
conn.close()
print("Migration v3 completed successfully.")
