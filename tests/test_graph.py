import pytest
import sqlite3
import os
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from src.graph import build_graph
from src.state import AgentState

@pytest.fixture
def memory_saver():
    return MemorySaver()

def get_graph(memory_saver):
    builder = build_graph()
    app = builder.compile(checkpointer=memory_saver)
    return app

def test_low_trust_action_interrupts(setup_test_db, override_db_path_env, memory_saver):
    db_path = os.environ.get("DATABASE_PATH")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO content_queue (id, content, status) VALUES (?, ?, ?)",
        ("post_001", "Hello World", "pending")
    )
    cursor.execute(
        "INSERT OR REPLACE INTO trust_metrics (action_type, successful_executions) VALUES (?, ?)",
        ("purge_stale", 0)
    )
    conn.commit()
    conn.close()
    
    app = get_graph(memory_saver)
    config = {"configurable": {"thread_id": "test_thread_1"}}
    
    initial_state = {
        "proposed_actions": [
            {"type": "purge_stale", "row_ids": ["post_001"]}
        ]
    }
    
    app.invoke(initial_state, config)
    state = app.get_state(config)
    
    assert len(state.next) > 0
    assert state.next[0] == "human_review_node"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_queue WHERE id = 'post_001'")
    assert cursor.fetchone() is not None
    conn.close()

def test_approved_action_executes(setup_test_db, override_db_path_env, memory_saver):
    db_path = os.environ.get("DATABASE_PATH")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO content_queue (id, content, status) VALUES (?, ?, ?)",
        ("post_002", "Hello World 2", "pending")
    )
    cursor.execute(
        "INSERT OR REPLACE INTO trust_metrics (action_type, successful_executions) VALUES (?, ?)",
        ("purge_stale", 0)
    )
    conn.commit()
    conn.close()
    
    app = get_graph(memory_saver)
    config = {"configurable": {"thread_id": "test_thread_2"}}
    initial_state = {
        "proposed_actions": [
            {"type": "purge_stale", "row_ids": ["post_002"]}
        ]
    }
    app.invoke(initial_state, config)
    
    app.invoke(Command(resume="Y"), config)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_queue WHERE id = 'post_002'")
    row = cursor.fetchone()
    
    cursor.execute("SELECT successful_executions FROM trust_metrics WHERE action_type = 'purge_stale'")
    trust = cursor.fetchone()[0]
    conn.close()
    
    assert row is None
    assert trust == 1

def test_rejected_action_does_not_execute(setup_test_db, override_db_path_env, memory_saver):
    db_path = os.environ.get("DATABASE_PATH")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO content_queue (id, content, status) VALUES (?, ?, ?)",
        ("post_003", "Hello World 3", "pending")
    )
    cursor.execute(
        "INSERT OR REPLACE INTO trust_metrics (action_type, successful_executions) VALUES (?, ?)",
        ("purge_stale", 0)
    )
    conn.commit()
    conn.close()
    
    app = get_graph(memory_saver)
    config = {"configurable": {"thread_id": "test_thread_3"}}
    initial_state = {
        "proposed_actions": [
            {"type": "purge_stale", "row_ids": ["post_003"]}
        ]
    }
    app.invoke(initial_state, config)
    
    app.invoke(Command(resume="N"), config)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_queue WHERE id = 'post_003'")
    row = cursor.fetchone()
    
    cursor.execute("SELECT successful_executions FROM trust_metrics WHERE action_type = 'purge_stale'")
    trust = cursor.fetchone()[0]
    conn.close()
    
    assert row is not None
    assert trust == 0

def test_trusted_action_executes_without_interruption(setup_test_db, override_db_path_env, memory_saver):
    db_path = os.environ.get("DATABASE_PATH")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO content_queue (id, content, status) VALUES (?, ?, ?)",
        ("post_004", "Hello World 4", "pending")
    )
    cursor.execute(
        "INSERT OR REPLACE INTO trust_metrics (action_type, successful_executions) VALUES (?, ?)",
        ("purge_stale", 5)
    )
    conn.commit()
    conn.close()
    
    app = get_graph(memory_saver)
    config = {"configurable": {"thread_id": "test_thread_4"}}
    initial_state = {
        "proposed_actions": [
            {"type": "purge_stale", "row_ids": ["post_004"]}
        ]
    }
    app.invoke(initial_state, config)
    
    state = app.get_state(config)
    assert len(state.next) == 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_queue WHERE id = 'post_004'")
    row = cursor.fetchone()
    conn.close()
    
    assert row is None
