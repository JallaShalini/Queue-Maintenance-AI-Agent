import sqlite3
import os
import config.settings as settings

def get_connection(db_path=None):
    if db_path is None:
        db_path = settings.DATABASE_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS content_queue (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS action_log (
        action_id TEXT PRIMARY KEY,
        action_type TEXT NOT NULL,
        target_row_id TEXT NOT NULL,
        previous_state_json TEXT NOT NULL,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trust_metrics (
        action_type TEXT PRIMARY KEY,
        successful_executions INTEGER DEFAULT 0
    )
    """)
    
    # Initialize basic types
    for action_type in ["mark_posted", "retry_row", "purge_stale"]:
        cursor.execute("""
        INSERT OR IGNORE INTO trust_metrics (action_type, successful_executions)
        VALUES (?, 0)
        """, (action_type,))
        
    conn.commit()
    conn.close()
