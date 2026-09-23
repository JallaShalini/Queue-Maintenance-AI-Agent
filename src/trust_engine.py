import sqlite3
import config.settings as settings

def check_trust(action_type: str, db_path: str = None) -> bool:
    if db_path is None:
        db_path = settings.DATABASE_PATH
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT successful_executions FROM trust_metrics WHERE action_type = ?", (action_type,))
    result = cursor.fetchone()
    conn.close()
    
    count = result[0] if result else 0
    return count >= settings.TRUST_THRESHOLD

def increment_trust(action_type: str, db_path: str = None):
    if db_path is None:
        db_path = settings.DATABASE_PATH
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE trust_metrics SET successful_executions = successful_executions + 1 WHERE action_type = ?", (action_type,))
    conn.commit()
    conn.close()
