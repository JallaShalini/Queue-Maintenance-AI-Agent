import sqlite3
from src.trust_engine import check_trust, increment_trust

def test_trust_engine_logic(override_db_path_env, monkeypatch):
    monkeypatch.setattr("config.settings.TRUST_THRESHOLD", 3)
    db_path = override_db_path_env
    
    assert check_trust("unknown_action", db_path) is False
    
    # By default, setup initializes with 0 which should be False ( < 3 )
    assert check_trust("purge_stale", db_path) is False
    
    increment_trust("purge_stale", db_path)
    assert check_trust("purge_stale", db_path) is False
    
    increment_trust("purge_stale", db_path)
    increment_trust("purge_stale", db_path)
    assert check_trust("purge_stale", db_path) is True
