import sqlite3
from pathlib import Path


DB_PATH = Path("data/processed/app.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


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

    connection.commit()
    connection.close()
