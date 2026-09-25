import sqlite3
import os
import sys

# Update path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph.checkpoint.memory import MemorySaver  # type: ignore
from langgraph.types import Command  # type: ignore
import config.settings as settings
from src.database import init_db
from src.graph import build_graph
from src.operations import restore_from_log

def run_simulation():
    os.environ["MOCK_LLM"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    db_path = settings.DATABASE_PATH
    init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Seed 10 dummy rows
    for i in range(10):
        cursor.execute(
            "INSERT OR REPLACE INTO content_queue (id, content, status) VALUES (?, ?, ?)",
            (f"post_{i}", f"Old stale post {i}", "pending")
        )
        
    # Reset trust for purge_stale to 0
    cursor.execute("UPDATE trust_metrics SET successful_executions = 0 WHERE action_type = 'purge_stale'")
    conn.commit()
    conn.close()
    
    # Build graph
    memory_saver = MemorySaver()
    app = build_graph().compile(checkpointer=memory_saver)
    config = {"configurable": {"thread_id": "sim_thread_1"}}
    
    # Instead of hitting LLM, we just simulate the LLM output directly into the state
    initial_state = {
        "messages": [{"role": "user", "content": "Cleanup the queue, remove anything stale or old."}],
        "proposed_actions": [
            {"type": "purge_stale", "row_ids": [f"post_{i}" for i in range(10)]}
        ]
    }
    
    print("Submitting ambiguous cleanup command...")
    app.invoke(initial_state, config)
    
    state = app.get_state(config)
    
    # Assert interception
    assert len(state.next) > 0, "Graph failed to interrupt!"
    assert state.next[0] == "human_review_node", "Graph did not route to human review!"
    print("Graph successfully intercepted destructive action.")
    
    # Assert no data was deleted yet
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM content_queue")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 10, "Data was deleted before approval!"
    print("Rows remained intact pending approval.")
    
    # Approve the action deliberately to test restore
    print("Approving destructive action...")
    app.invoke(Command(resume="Y"), config)
    
    # Data should be gone now
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM content_queue WHERE content LIKE 'Old stale post%'")
    count = cursor.fetchone()[0]
    assert count == 0, "Deletion failed!"
    print("Destructive action processed.")
    
    # Find action logs
    cursor.execute("SELECT action_id FROM action_log WHERE target_row_id LIKE 'post_%'")
    logs = cursor.fetchall()
    conn.close()
    
    print("Restoring from logs...")
    for log in logs:
        restore_from_log(log[0], db_path)
        
    # Verify all restored
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM content_queue WHERE content LIKE 'Old stale post%'")
    restored_count = cursor.fetchone()[0]
    conn.close()
    
    assert restored_count == 10, f"Restore failed, only have {restored_count}/10 rows!"
    print("All 10 rows successfully recovered!")

if __name__ == "__main__":
    run_simulation()
