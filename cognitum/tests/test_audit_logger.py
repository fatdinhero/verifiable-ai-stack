import pytest
import json
import sqlite3
import os
from cognitum_audit.audit_logger import AuditLogger

@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_audit.db")

@pytest.fixture
def logger(temp_db_path):
    logger = AuditLogger(db_path=temp_db_path)
    yield logger
    logger.close()

def test_initialization_creates_database_and_table(temp_db_path):
    assert not os.path.exists(temp_db_path)
    logger = AuditLogger(db_path=temp_db_path)
    assert os.path.exists(temp_db_path)
    logger.close()

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log';")
    assert cursor.fetchone() is not None
    conn.close()

def test_log_inserts_entry(logger, temp_db_path):
    logger.log(
        agent="test_agent",
        action="test_action",
        result={"key": "value"},
        confidence=0.8
    )

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT * FROM audit_log;")
    rows = cursor.fetchall()
    assert len(rows) == 1

    row = rows[0]
    assert row[1] is not None  # timestamp
    assert row[2] == "test_agent"
    assert row[3] == "test_action"
    assert json.loads(row[4]) == {"key": "value"}
    assert row[5] == 0.8
    conn.close()

def test_log_multiple_entries(logger, temp_db_path):
    for i in range(3):
        logger.log(
            agent=f"agent_{i}",
            action=f"action_{i}",
            result={"index": i},
            confidence=0.5
        )

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM audit_log;")
    count = cursor.fetchone()[0]
    assert count == 3
    conn.close()

def test_log_invalid_confidence_raises_error(logger):
    with pytest.raises(ValueError):
        logger.log("agent", "action", {}, 1.5)

    with pytest.raises(ValueError):
        logger.log("agent", "action", {}, -0.1)

def test_log_invalid_result_type_raises_error(logger):
    with pytest.raises(TypeError):
        logger.log("agent", "action", [1, 2, 3], 0.5)

    with pytest.raises(TypeError):
        logger.log("agent", "action", "not a dict", 0.5)

def test_log_with_complex_result(logger, temp_db_path):
    complex_result = {
        "nested": {"a": [1, 2, 3], "b": True},
        "null_value": None,
        "string_with_unicode": "日本語テスト"
    }
    logger.log("agent", "complex_action", complex_result, 0.75)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT result_json FROM audit_log;")
    row = cursor.fetchone()
    parsed = json.loads(row[0])
    assert parsed == complex_result
    conn.close()

def test_log_stores_utc_timestamp(logger, temp_db_path):
    before = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    logger.log("agent", "action", {}, 1.0)
    after = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT timestamp FROM audit_log;")
    stored_ts = cursor.fetchone()[0]
    assert before <= stored_ts <= after
    conn.close()

def test_close_connection(temp_db_path):
    logger = AuditLogger(db_path=temp_db_path)
    logger.log("agent", "action", {}, 0.5)
    logger.close()

    # After closing, trying to log should raise an error
    with pytest.raises(Exception):
        logger.log("agent", "action", {}, 0.5)

def test_context_manager(temp_db_path):
    with AuditLogger(db_path=temp_db_path) as logger:
        logger.log("agent", "action", {}, 0.5)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM audit_log;")
        assert cursor.fetchone()[0] == 1
        conn.close()

    # After exiting context, connection should be closed
    with pytest.raises(Exception):
        logger.log("agent", "action", {}, 0.5)

def test_repr(logger):
    assert repr(logger).startswith("AuditLogger(db_path=")

def test_wal_journal_mode(temp_db_path):
    logger = AuditLogger(db_path=temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    assert mode.upper() == "WAL"
    conn.close()
    logger.close()

def test_unique_ids(temp_db_path):
    logger = AuditLogger(db_path=temp_db_path)
    ids = set()
    for i in range(10):
        logger.log("agent", "action", {}, 0.5)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.execute("SELECT id FROM audit_log ORDER BY rowid DESC LIMIT 1;")
        last_id = cursor.fetchone()[0]
        ids.add(last_id)
        conn.close()
    assert len(ids) == 10
    logger.close()

def test_default_db_path():
    # Clean up any default database
    if os.path.exists("cognitum_audit.db"):
        os.remove("cognitum_audit.db")
    
    try:
        logger = AuditLogger()
        assert os.path.exists("cognitum_audit.db")
        logger.close()
    finally:
        if os.path.exists("cognitum_audit.db"):
            os.remove("cognitum_audit.db")