import sqlite3
import json
from pathlib import Path
from poisv.incident_log import IncidentRecord

DB_PATH = Path("/opt/poisv/data/incidents.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

def load_all() -> dict:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT incident_id, data FROM incidents").fetchall()
    con.close()
    return {iid: IncidentRecord(**json.loads(data)) for iid, data in rows}

def save_incident(record: IncidentRecord):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR REPLACE INTO incidents (incident_id, data) VALUES (?, ?)",
        (record.incident_id, record.model_dump_json())
    )
    con.commit()
    con.close()

def delete_incident(incident_id: str):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM incidents WHERE incident_id = ?", (incident_id,))
    con.commit()
    con.close()