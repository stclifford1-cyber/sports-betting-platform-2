import sqlite3

DATABASE_PATH = "data/processed/app.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_match_by_id(match_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id,
               player_1,
               player_2,
               tournament,
               start_time,
               odds_player_1,
               odds_player_2
        FROM matches
        WHERE id = ?
        """,
        (match_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)
