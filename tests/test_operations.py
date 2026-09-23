import sqlite3
from src.operations import execute_mutation

def test_execute_mutation_logs_state(override_db_path_env):
    db_path = override_db_path_env
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO content_queue (id, content, status) VALUES (?, ?, ?)",
        ("post_1", "Test content", "pending")
    )
    conn.commit()
    conn.close()
    
    result = execute_mutation("mark_posted", "post_1", {"status": "posted"}, db_path)
    assert result["success"] is True
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT target_row_id, previous_state_json FROM action_log WHERE action_id = ?", (result["action_id"],))
    log = cursor.fetchone()
    conn.close()
    
    assert log is not None
    assert log[0] == "post_1"
    assert "pending" in log[1]
