import json
import sqlite3
from pathlib import Path
from datetime import datetime


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
            status TEXT NOT NULL DEFAULT 'pending',
            winner TEXT,
            completed_at TEXT,
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

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS strategy_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            request_json TEXT NOT NULL,
            ranking_method_json TEXT NOT NULL,
            summary_json TEXT NOT NULL,
            best_result_json TEXT,
            results_json TEXT NOT NULL
        )
        """
    )

    ensure_match_result_columns(connection)

    connection.commit()
    connection.close()


def create_slate(source: str):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO slates (source, created_at)
            VALUES (?, ?)
            """,
            (source, datetime.utcnow().isoformat()),
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "source": source,
        }

    finally:
        connection.close()


def create_match(
    slate_id: int,
    player_1: str,
    player_2: str,
    tournament: str,
    start_time: str,
    odds_player_1: float,
    odds_player_2: float,
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO matches (
                slate_id,
                player_1,
                player_2,
                tournament,
                start_time,
                odds_player_1,
                odds_player_2
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slate_id,
                player_1,
                player_2,
                tournament,
                start_time,
                odds_player_1,
                odds_player_2,
            ),
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "slate_id": slate_id,
            "player_1": player_1,
            "player_2": player_2,
            "tournament": tournament,
            "start_time": start_time,
            "odds_player_1": odds_player_1,
            "odds_player_2": odds_player_2,
            "status": "pending",
            "winner": None,
            "completed_at": None,
        }

    finally:
        connection.close()


def record_match_result(match_id: int, winner: str):
    connection = get_connection()

    try:
        completed_at = datetime.utcnow().isoformat()

        cursor = connection.execute(
            """
            UPDATE matches
            SET status = ?, winner = ?, completed_at = ?
            WHERE id = ?
            """,
            ("completed", winner, completed_at, match_id),
        )

        connection.commit()

        if cursor.rowcount == 0:
            return {"error": f"match_id {match_id} not found"}

        row = connection.execute(
            """
            SELECT
                id,
                slate_id,
                player_1,
                player_2,
                tournament,
                start_time,
                odds_player_1,
                odds_player_2,
                status,
                winner,
                completed_at
            FROM matches
            WHERE id = ?
            """,
            (match_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def create_strategy_experiment(
    experiment_request: dict,
    ranking_method: dict,
    summary: dict,
    best_result: dict | None,
    results: list,
):
    connection = get_connection()

    try:
        created_at = datetime.utcnow().isoformat()

        cursor = connection.execute(
            """
            INSERT INTO strategy_experiments (
                created_at,
                request_json,
                ranking_method_json,
                summary_json,
                best_result_json,
                results_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                json.dumps(experiment_request),
                json.dumps(ranking_method),
                json.dumps(summary),
                json.dumps(best_result) if best_result is not None else None,
                json.dumps(results),
            ),
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "created_at": created_at,
        }

    finally:
        connection.close()


def list_strategy_experiments():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                request_json,
                summary_json,
                best_result_json
            FROM strategy_experiments
            ORDER BY id DESC
            """
        ).fetchall()

        experiments = []
        for row in rows:
            request_data = json.loads(row["request_json"])
            summary_data = json.loads(row["summary_json"])
            best_result_data = json.loads(row["best_result_json"]) if row["best_result_json"] else None

            experiments.append(
                {
                    "experiment_id": row["id"],
                    "created_at": row["created_at"],
                    "experiment_request": request_data,
                    "summary": summary_data,
                    "best_result": best_result_data,
                }
            )

        return experiments

    finally:
        connection.close()


def get_strategy_experiment(experiment_id: int):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                created_at,
                request_json,
                ranking_method_json,
                summary_json,
                best_result_json,
                results_json
            FROM strategy_experiments
            WHERE id = ?
            """,
            (experiment_id,),
        ).fetchone()

        if row is None:
            return {"error": f"experiment_id {experiment_id} not found"}

        return {
            "experiment_id": row["id"],
            "created_at": row["created_at"],
            "experiment_request": json.loads(row["request_json"]),
            "ranking_method": json.loads(row["ranking_method_json"]),
            "summary": json.loads(row["summary_json"]),
            "best_result": json.loads(row["best_result_json"]) if row["best_result_json"] else None,
            "results": json.loads(row["results_json"]),
        }

    finally:
        connection.close()
