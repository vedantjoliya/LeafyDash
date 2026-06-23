import sqlite3
import os

db_path = "database.db"

if not os.path.exists(db_path):
    print("Database file not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Adding customer_address column to sales...")
    cursor.execute("ALTER TABLE sales ADD COLUMN customer_address TEXT;")
    print("Added customer_address column.")
except Exception as e:
    print(f"customer_address already exists or error: {e}")

try:
    print("Creating employees table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        salary REAL NOT NULL,
        email TEXT,
        phone TEXT,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)
    print("Created employees table.")
except Exception as e:
    print(f"Failed to create employees table: {e}")

try:
    print("Creating operational_expenses table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operational_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)
    print("Created operational_expenses table.")
except Exception as e:
    print(f"Failed to create operational_expenses table: {e}")

conn.commit()
conn.close()
print("Migration v2 completed successfully.")
