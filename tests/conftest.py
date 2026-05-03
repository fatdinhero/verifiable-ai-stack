"""Test fixtures — isolate DB state."""
import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def clean_db():
    """Clean history.db before each test to avoid cross-contamination."""
    db = Path.home() / "COS" / "daysensos" / "history.db"
    if db.exists():
        db.unlink()
    yield
    if db.exists():
        db.unlink()
