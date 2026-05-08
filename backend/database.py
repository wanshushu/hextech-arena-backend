"""
HexTech Arena Backend — SQLite database layer
"""
import sqlite3
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "hextech.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS champions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            title TEXT DEFAULT '',
            tier TEXT DEFAULT '',
            winrate TEXT DEFAULT '',
            pickrate TEXT DEFAULT '',
            patch TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS augments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            champion_id TEXT NOT NULL,
            name TEXT NOT NULL,
            tier TEXT DEFAULT '',
            winrate TEXT DEFAULT '',
            pickrate TEXT DEFAULT '',
            position INTEGER DEFAULT 0,
            FOREIGN KEY (champion_id) REFERENCES champions(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'core',
            champion_id TEXT,
            position INTEGER DEFAULT 0,
            FOREIGN KEY (champion_id) REFERENCES champions(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'started',
            tiers_found TEXT DEFAULT '',
            champions_crawled INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def upsert_champion(data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO champions (id, name, title, tier, winrate, pickrate, patch, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("id", ""),
        data.get("name", ""),
        data.get("title", ""),
        data.get("tier", ""),
        data.get("winrate", ""),
        data.get("pickrate", ""),
        data.get("patch", ""),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def upsert_augments(champion_id: str, augments: List[Dict]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM augments WHERE champion_id = ?", (champion_id,))
    for i, aug in enumerate(augments):
        cursor.execute("""
            INSERT INTO augments (champion_id, name, tier, winrate, pickrate, position)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (champion_id, aug.get("name", ""), aug.get("tier", ""),
              aug.get("winrate", ""), aug.get("pickrate", ""), i))
    conn.commit()
    conn.close()


def upsert_items(champion_id: str, category: str, items: List[str]):
    conn = get_connection()
    cursor = conn.cursor()
    for i, name in enumerate(items):
        cursor.execute("""
            INSERT OR REPLACE INTO items (name, category, champion_id, position)
            VALUES (?, ?, ?, ?)
        """, (name, category, champion_id, i))
    conn.commit()
    conn.close()


def get_all_champions(tier: Optional[str] = None, search: Optional[str] = None,
                       limit: int = 100, offset: int = 0) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM champions WHERE 1=1"
    params: List[Any] = []

    if tier:
        query += " AND tier = ?"
        params.append(tier)

    if search:
        query += " AND (name LIKE ? OR title LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY CASE tier WHEN 'T1' THEN 1 WHEN 'T2' THEN 2 WHEN 'T3' THEN 3 WHEN 'T4' THEN 4 ELSE 5 END"
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_champion_by_id(champ_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM champions WHERE id = ?", (champ_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    champion = dict(row)

    cursor.execute("SELECT * FROM augments WHERE champion_id = ? ORDER BY position", (champ_id,))
    champion["top_augments"] = [dict(r) for r in cursor.fetchall()]

    for category, label in [("core", "core_items"), ("situational", "situational_items"), ("starting", "starting_items")]:
        cursor.execute(
            "SELECT name FROM items WHERE champion_id = ? AND category = ? ORDER BY position",
            (champ_id, category)
        )
        champion[label] = [r["name"] for r in cursor.fetchall()]

    conn.close()
    return champion


def get_tier_list() -> Dict[str, List[Dict]]:
    conn = get_connection()
    cursor = conn.cursor()
    tiers: Dict[str, List[Dict]] = {"T1": [], "T2": [], "T3": [], "T4": [], "T5": []}

    for tier in ["T1", "T2", "T3", "T4", "T5"]:
        cursor.execute(
            "SELECT id, name, tier, winrate, pickrate FROM champions WHERE tier = ? ORDER BY winrate DESC",
            (tier,)
        )
        tiers[tier] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return tiers


def get_champion_count(tier: Optional[str] = None, search: Optional[str] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM champions WHERE 1=1"
    params: List[Any] = []

    if tier:
        query += " AND tier = ?"
        params.append(tier)
    if search:
        query += " AND (name LIKE ? OR title LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()
    return count


def log_refresh(status: str, tiers_found: str = "", champions_crawled: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO refresh_log (timestamp, status, tiers_found, champions_crawled)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().isoformat(), status, tiers_found, champions_crawled))
    conn.commit()
    conn.close()


def get_last_refresh() -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM refresh_log ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def set_meta(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_meta(key: str) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None
