import sqlite3
from src.operations import execute_mutation, restore_from_log

def test_restore_from_log(override_db_path_env):
    db_path = override_db_path_env
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO content_queue (id, content, status) VALUES (?, ?, ?)",
        ("post_x", "To be deleted", "pending")
    )
    conn.commit()
    conn.close()
    
    # Delete the row
    result = execute_mutation("purge_stale", "post_x", {}, db_path)
    assert result["success"] is True
    
    # Verify row is deleted
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_queue WHERE id = 'post_x'")
    assert cursor.fetchone() is None
    conn.close()
    
    # Restore
    assert restore_from_log(result["action_id"], db_path) is True
    
    # Verify row exists with initial values
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_queue WHERE id = 'post_x'")
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row[1] == "To be deleted"
