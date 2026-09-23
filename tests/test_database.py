import sqlite3

def test_database_initialization(override_db_path_env):
    db_path = override_db_path_env
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    
    assert "content_queue" in tables
    assert "action_log" in tables
    assert "trust_metrics" in tables
    
    # Check if trust_metrics has initialized values
    cursor.execute("SELECT action_type FROM trust_metrics")
    action_types = {row[0] for row in cursor.fetchall()}
    assert "mark_posted" in action_types
    assert "retry_row" in action_types
    assert "purge_stale" in action_types
    
    conn.close()
