from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict


DB_PATH = Path("data/processed/app.db")


def calculate_player_score(match_id: int, player_name: str) -> Dict[str, Any]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT
                match_id,
                player_name,
                player_ranking,
                opponent_ranking,
                recent_wins,
                head_to_head_wins
            FROM player_match_features
            WHERE match_id = ? AND player_name = ?
            """,
            (match_id, player_name),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise ValueError(
            f"No feature row found for match_id={match_id}, player_name='{player_name}'"
        )

    player_ranking = row["player_ranking"]
    opponent_ranking = row["opponent_ranking"]
    recent_wins = row["recent_wins"]
    head_to_head_wins = row["head_to_head_wins"]

    missing_fields = [
        field_name
        for field_name, field_value in {
            "player_ranking": player_ranking,
            "opponent_ranking": opponent_ranking,
            "recent_wins": recent_wins,
            "head_to_head_wins": head_to_head_wins,
        }.items()
        if field_value is None
    ]

    if missing_fields:
        raise ValueError(
            "Cannot calculate score because required feature values are missing: "
            + ", ".join(missing_fields)
        )

    score = (
        (opponent_ranking - player_ranking)
        + recent_wins
        + head_to_head_wins
    )

    return {
        "match_id": row["match_id"],
        "player_name": row["player_name"],
        "score": score,
        "inputs": {
            "player_ranking": player_ranking,
            "opponent_ranking": opponent_ranking,
            "recent_wins": recent_wins,
            "head_to_head_wins": head_to_head_wins,
        },
    }
