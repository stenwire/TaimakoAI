import sqlite3
import os

db_path = 'sql_app.db'
print(f"Connecting to {db_path}...")

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found!")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check if column exists first to avoid error if run multiple times
    cursor.execute("PRAGMA table_info(chat_sessions)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'sentiment_score' in columns:
        print("Column 'sentiment_score' already exists.")
    else:
        print("Adding column 'sentiment_score'...")
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN sentiment_score FLOAT")
        conn.commit()
        print("Column added successfully.")
        
except Exception as e:
    print(f"Migration Error: {e}")
finally:
    if conn:
        conn.close()
