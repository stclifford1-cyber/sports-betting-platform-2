import sqlite3
from pathlib import Path


DB_PATH = Path("data/processed/app.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_match_result_columns(connection):
    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(matches)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "status" not in existing_columns:
        cursor.execute(
            "ALTER TABLE matches ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'"
        )

    if "winner" not in existing_columns:
        cursor.execute(
            "ALTER TABLE matches ADD COLUMN winner TEXT"
        )

    if "completed_at" not in existing_columns:
        cursor.execute(
            "ALTER TABLE matches ADD COLUMN completed_at TEXT"
        )


def init_db():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS slates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slate_id INTEGER NOT NULL,
            player_1 TEXT NOT NULL,
            player_2 TEXT NOT NULL,
            tournament TEXT NOT NULL,
            start_time TEXT NOT NULL,
            odds_player_1 REAL NOT NULL,
            odds_player_2 REAL NOT NULL,
            FOREIGN KEY (slate_id) REFERENCES slates(id)
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            selection TEXT NOT NULL,
            odds REAL NOT NULL,
            stake REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            profit_loss REAL,
            placed_at TEXT NOT NULL,
            settled_at TEXT,
            FOREIGN KEY (match_id) REFERENCES matches(id)
        )
        """
    )

    ensure_match_result_columns(connection)

    connection.commit()
    connection.close()
