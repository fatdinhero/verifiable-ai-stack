import pytest
import os
import json
import time
import tempfile
from cognitum_memory.memory_store import MemoryStore


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database file path."""
    return str(tmp_path / "test_memory.db")


@pytest.fixture
def store(temp_db_path):
    """Create a MemoryStore instance with a temporary database."""
    return MemoryStore(db_path=temp_db_path)


def test_initialization_creates_database(temp_db_path):
    """Test that initialization creates the database file and table."""
    assert not os.path.exists(temp_db_path)
    store = MemoryStore(db_path=temp_db_path)
    assert os.path.exists(temp_db_path)


def test_save_and_load(store):
    """Test basic save and load functionality."""
    test_data = {"key": "value", "number": 42, "nested": {"a": [1, 2]}}
    store.save("run1", test_data)
    
    loaded = store.load("run1")
    assert loaded == test_data


def test_save_overwrites_existing(store):
    """Test that saving with an existing run_id overwrites previous data."""
    store.save("run1", {"a": 1})
    store.save("run1", {"b": 2})
    
    loaded = store.load("run1")
    assert loaded == {"b": 2}


def test_load_nonexistent_raises_keyerror(store):
    """Test that loading a non-existent run_id raises KeyError."""
    with pytest.raises(KeyError, match="run_id.*nonexistent"):
        store.load("nonexistent")


def test_timestamp_is_recorded(temp_db_path):
    """Test that timestamps are recorded in the database."""
    store = MemoryStore(db_path=temp_db_path)
    
    before = time.time()
    store.save("run1", {"test": True})
    after = time.time()
    
    import sqlite3
    with sqlite3.connect(temp_db_path) as conn:
        cursor = conn.execute("SELECT timestamp FROM memory WHERE run_id = ?", ("run1",))
        row = cursor.fetchone()
        
    assert before <= row[0] <= after


def test_default_db_path(monkeypatch, tmp_path):
    """Test that default database path is used when not specified."""
    # Change to temporary directory to avoid polluting the actual working directory
    monkeypatch.chdir(tmp_path)
    
    store = MemoryStore()
    assert store.db_path == "cognitum_memory.db"
    assert os.path.exists("cognitum_memory.db")
    
    # Cleanup
    os.remove("cognitum_memory.db")


def test_multiple_entries(store):
    """Test storing and retrieving multiple entries."""
    store.save("run1", {"id": 1})
    store.save("run2", {"id": 2})
    store.save("run3", {"id": 3})
    
    assert store.load("run1") == {"id": 1}
    assert store.load("run2") == {"id": 2}
    assert store.load("run3") == {"id": 3}


def test_complex_data_serialization(store):
    """Test that complex nested structures are properly serialized."""
    complex_data = {
        "list": [1, 2, 3],
        "dict": {"nested": {"deep": [True, None, 3.14]}},
        "string": "hello world",
        "null": None
    }
    
    store.save("complex", complex_data)
    loaded = store.load("complex")
    assert loaded == complex_data