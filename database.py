"""
Database module for the Flagging Unregistered Vehicles system.
Uses SQLite for storing registered vehicles and detection logs.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicles.db")


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database tables and seed sample data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create registered_vehicles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registered_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT UNIQUE NOT NULL,
            owner_name TEXT NOT NULL,
            vehicle_type TEXT NOT NULL DEFAULT 'Car',
            added_on DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create detection_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            is_registered BOOLEAN DEFAULT 0,
            image_path TEXT,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Seed sample registered vehicles if table is empty
    cursor.execute("SELECT COUNT(*) FROM registered_vehicles")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_vehicles = [
            ("MH31AB1234", "Krushna Raut", "Car"),
            ("MH31CD5678", "Vikram Jaiswal", "Car"),
            ("MH31EF9012", "Sankalp Choubey", "Bike"),
            ("MH12GH3456", "Rajesh Kumar", "Car"),
            ("MH14JK7890", "Priya Sharma", "Bike"),
            ("MH40LM2345", "Amit Patil", "Truck"),
            ("DL01NO6789", "Suresh Verma", "Car"),
            ("MH31PQ4567", "Neha Deshmukh", "Car"),
            ("KA05RS8901", "Arun Joshi", "Bike"),
            ("MH49TU2345", "Meena Gupta", "Car"),
            ("GJ01VW6789", "Ravi Patel", "Truck"),
            ("MH20XY0123", "Pooja Singh", "Car"),
        ]

        cursor.executemany(
            "INSERT INTO registered_vehicles (plate_number, owner_name, vehicle_type) VALUES (?, ?, ?)",
            sample_vehicles,
        )
        conn.commit()
        print(f"[DB] Seeded {len(sample_vehicles)} sample registered vehicles.")

    conn.close()


# ─── Registered Vehicles CRUD ──────────────────────────────────────

def get_all_vehicles():
    """Get all registered vehicles."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM registered_vehicles ORDER BY added_on DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_vehicle(plate_number, owner_name, vehicle_type="Car"):
    """Add a new vehicle to the registered database."""
    plate_number = plate_number.upper().replace(" ", "").replace("-", "")
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO registered_vehicles (plate_number, owner_name, vehicle_type) VALUES (?, ?, ?)",
            (plate_number, owner_name, vehicle_type),
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Vehicle {plate_number} registered successfully."}
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "message": f"Vehicle {plate_number} is already registered."}


def delete_vehicle(plate_number):
    """Remove a vehicle from the registered database."""
    plate_number = plate_number.upper().replace(" ", "").replace("-", "")
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM registered_vehicles WHERE plate_number = ?", (plate_number,)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    if deleted:
        return {"success": True, "message": f"Vehicle {plate_number} removed."}
    else:
        return {"success": False, "message": f"Vehicle {plate_number} not found."}


def is_vehicle_registered(plate_number):
    """Check if a plate number exists in the registered database."""
    plate_number = plate_number.upper().replace(" ", "").replace("-", "")
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM registered_vehicles WHERE plate_number = ?", (plate_number,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Detection Logs ────────────────────────────────────────────────

def add_detection_log(plate_number, confidence, is_registered, image_path):
    """Log a detection event."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO detection_logs 
           (plate_number, confidence, is_registered, image_path) 
           VALUES (?, ?, ?, ?)""",
        (plate_number, confidence, is_registered, image_path),
    )
    conn.commit()
    conn.close()


def get_detection_logs(limit=50):
    """Get recent detection logs."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM detection_logs ORDER BY detected_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats():
    """Get dashboard statistics."""
    conn = get_connection()

    total_detections = conn.execute(
        "SELECT COUNT(*) FROM detection_logs"
    ).fetchone()[0]

    registered_hits = conn.execute(
        "SELECT COUNT(*) FROM detection_logs WHERE is_registered = 1"
    ).fetchone()[0]

    flagged_count = conn.execute(
        "SELECT COUNT(*) FROM detection_logs WHERE is_registered = 0"
    ).fetchone()[0]

    total_vehicles = conn.execute(
        "SELECT COUNT(*) FROM registered_vehicles"
    ).fetchone()[0]

    # Recent flagged vehicles (last 10)
    recent_flagged = conn.execute(
        """SELECT plate_number, detected_at FROM detection_logs 
           WHERE is_registered = 0 ORDER BY detected_at DESC LIMIT 10"""
    ).fetchall()

    conn.close()

    return {
        "total_detections": total_detections,
        "registered_hits": registered_hits,
        "flagged_count": flagged_count,
        "total_registered_vehicles": total_vehicles,
        "recent_flagged": [dict(r) for r in recent_flagged],
    }


# Initialize DB on import
if __name__ == "__main__":
    init_db()
    print("[DB] Database initialized successfully.")
    print(f"[DB] Registered vehicles: {len(get_all_vehicles())}")
