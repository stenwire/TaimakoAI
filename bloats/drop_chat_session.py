import sqlite3

def clean_db():
    conn = sqlite3.connect('sql_app.db')
    cursor = conn.cursor()
    
    try:
        print("Dropping chat_sessions table...")
        cursor.execute("DROP TABLE IF EXISTS chat_sessions")
        print("Dropped chat_sessions.")
    except Exception as e:
        print(f"Error dropping chat_sessions: {e}")

    # Dropping column in sqlite is tricky, usually requires recreating table. 
    # But since Alembic batch operations handle this, and the column might not exist if previous run failed halfway.
    # Actually, if previous run failed on FK creation, the column might be there.
    # But we can't easily drop column in pure sqlite without new table.
    # However, if we just drop chat_sessions, the FK constraint from guest_messages might linger if it wasn't named?
    # No, FK is on the guest_messages table.
    # If I don't drop the column `session_id` from `guest_messages`, Alembic might fail saying column exists or similar.
    # Alembic's `add_column` will fail if column exists.
    
    # Let's inspect if column exists.
    cursor.execute("PRAGMA table_info(guest_messages)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'session_id' in columns:
        print("Column session_id exists in guest_messages.")
        # We must remove it.
        # SQLite way: create new table without col, copy, drop old, rename.
        # Too risky to do manually?
        # Maybe I should just manually modify the migration file to skip adding column if exists?
        # NO, that's hacking.
        # Let's try to remove it using sqlite approach in this script.
        
        print("Recreating guest_messages without session_id...")
        # Get schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='guest_messages'")
        cursor.fetchone()[0]
        # create_sql has the session_id definition? maybe.
        # Easier: Rename table to _old, create new table (how to get schema?), copy, drop _old.
        # Actually, let's just use the fact that I can use python to do this cleanly if I had the Model.
        # But I don't want to load app stack.
        
        # Alternative: Just use alembic downgrade?
        # I can try `alembic downgrade e2cd2430b4a5` (the base revision).
        # But downgrading requires the migration to have been marked as done? It failed, so it's not marked?
        # Or maybe it IS marked but failed?
        # No, if it exits with 1, it probably didn't update alembic_version.
        pass
    else:
        print("Column session_id does not exist.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_db()
