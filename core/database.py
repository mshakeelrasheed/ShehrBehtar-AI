import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import SQLITE_DB_PATH

def get_db_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite civic ticket table schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS civic_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_uid TEXT UNIQUE NOT NULL,
        hazard_type TEXT NOT NULL,
        department TEXT NOT NULL,
        severity TEXT NOT NULL,
        sla_hours INTEGER NOT NULL,
        hazard_score INTEGER NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT NOT NULL,
        notes TEXT,
        materials_needed TEXT,
        image_path TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING',
        created_at TEXT NOT NULL,
        resolved_at TEXT
    );
    """)
    conn.commit()
    conn.close()

def insert_ticket(data: Dict[str, Any]) -> str:
    """Inserts a newly verified civic hazard ticket into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO civic_tickets (
        ticket_uid, hazard_type, department, severity, sla_hours,
        hazard_score, latitude, longitude, address, notes,
        materials_needed, image_path, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
    """, (
        data["ticket_uid"],
        data["hazard_type"],
        data["department"],
        data["severity"],
        data.get("sla_hours", 24),
        data.get("hazard_score", 50),
        data["latitude"],
        data["longitude"],
        data.get("address", "Bahawalpur Local Street"),
        data.get("notes", ""),
        data.get("materials_needed", ""),
        data.get("image_path", ""),
        timestamp
    ))
    conn.commit()
    conn.close()
    return data["ticket_uid"]

def get_all_tickets(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves tickets from the database with optional status filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status_filter and status_filter != "ALL":
        cursor.execute("SELECT * FROM civic_tickets WHERE status = ? ORDER BY id DESC", (status_filter,))
    else:
        cursor.execute("SELECT * FROM civic_tickets ORDER BY id DESC")
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_ticket_resolved(ticket_uid: str) -> bool:
    """Marks an active ticket as RESOLVED and records completion timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    UPDATE civic_tickets 
    SET status = 'RESOLVED', resolved_at = ? 
    WHERE ticket_uid = ?
    """, (timestamp, ticket_uid))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", SQLITE_DB_PATH)