import pytest
import os
import sys
import sqlite3
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import init_db

@pytest.fixture
def setup_test_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    
    # Initialize the tables
    init_db(path)
    
    yield path
    os.remove(path)

@pytest.fixture
def override_db_path_env(monkeypatch, setup_test_db):
    monkeypatch.setenv("DATABASE_PATH", setup_test_db)
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setattr("config.settings.DATABASE_PATH", setup_test_db)
    return setup_test_db
