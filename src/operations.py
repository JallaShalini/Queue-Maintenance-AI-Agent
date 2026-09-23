import sqlite3
import json
import uuid
from typing import Dict, Any, Optional
from langsmith import traceable
import config.settings as settings

@traceable
def execute_mutation(action_type: str, target_row_id: str, new_data: Dict[str, Any], db_path: str = None) -> Dict[str, Any]:
    if db_path is None:
        db_path = settings.DATABASE_PATH
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Fetch current row
        cursor.execute("SELECT * FROM content_queue WHERE id = ?", (target_row_id,))
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "error": f"Target row {target_row_id} not found."}
            
        previous_state = dict(row)
        previous_state_json = json.dumps(previous_state)
        
        # Write action log
        action_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO action_log (action_id, action_type, target_row_id, previous_state_json) VALUES (?, ?, ?, ?)",
            (action_id, action_type, target_row_id, previous_state_json)
        )
        
        # Commit log before mutation
        conn.commit()
        
        # Apply mutation
        if action_type == "purge_stale":
            cursor.execute("DELETE FROM content_queue WHERE id = ?", (target_row_id,))
        else:
            set_clause = ", ".join([f"{k} = ?" for k in new_data.keys()])
            values = list(new_data.values()) + [target_row_id]
            cursor.execute(f"UPDATE content_queue SET {set_clause} WHERE id = ?", values)
            
        conn.commit()
        return {"success": True, "action_id": action_id}
        
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

@traceable
def restore_from_log(action_id: str, db_path: str = None) -> bool:
    if db_path is None:
        db_path = settings.DATABASE_PATH
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT previous_state_json FROM action_log WHERE action_id = ?", (action_id,))
        result = cursor.fetchone()
        
        if not result:
            return False
            
        previous_state = json.loads(result[0])
        
        cursor.execute(
            "REPLACE INTO content_queue (id, content, status, created_at) VALUES (?, ?, ?, ?)",
            (previous_state['id'], previous_state['content'], previous_state['status'], previous_state['created_at'])
        )
        
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
