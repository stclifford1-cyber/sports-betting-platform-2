from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from pathlib import Path

from apps.api.services.feature_scoring import calculate_player_score


app = FastAPI(title="Sports Betting Strategy Development Platform")

DB_PATH = Path("data/processed/app.db")


class SlateCreate(BaseModel):
    source: str


class MatchCreate(BaseModel):
    slate_id: int
    player_1: str
    player_2: str
    tournament: str
    start_time: str
    odds_player_1: float
    odds_player_2: float


class BetCreate(BaseModel):
    match_id: int
    selected_player: str
    stake: float
    odds_taken: float


class BetSettlement(BaseModel):
    winner: str


class PlayerFeatureUpdate(BaseModel):
    surface: Optional[str] = None
    player_ranking: Optional[int] = None
    opponent_ranking: Optional[int] = None
    recent_wins: Optional[int] = None
    recent_losses: Optional[int] = None
    head_to_head_wins: Optional[int] = None
    head_to_head_losses: Optional[int] = None
    notes: Optional[str] = None


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.get("/")
def root():
    return {"status": "sports betting platform running"}


@app.get("/health")
def health():
    return {
        "project": "Sports Betting Strategy Development Platform",
        "focus": "tennis",
        "stage": "stage 7 feature scoring",
    }


@app.post("/slate")
def create_slate(payload: SlateCreate):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO slates (source)
        VALUES (?)
        """,
        (payload.source,),
    )

    slate_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return {
        "message": "Slate created successfully",
        "slate_id": slate_id,
        "source": payload.source,
    }


@app.get("/slate")
def list_slates():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT id, source, created_at
        FROM slates
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()

    return [dict(row) for row in rows]


@app.post("/matches")
def create_match(payload: MatchCreate):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO matches (
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL)
        """,
        (
            payload.slate_id,
            payload.player_1,
            payload.player_2,
            payload.tournament,
            payload.start_time,
            payload.odds_player_1,
            payload.odds_player_2,
        ),
    )

    match_id = cursor.lastrowid

    cursor.executemany(
        """
        INSERT INTO player_match_features (
            match_id,
            player_name
        )
        VALUES (?, ?)
        """,
        [
            (match_id, payload.player_1),
            (match_id, payload.player_2),
        ],
    )

    connection.commit()
    connection.close()

    return {
        "message": "Match created successfully",
        "match_id": match_id,
    }


@app.get("/matches")
def list_matches():
    connection = get_connection()
    rows = connection.execute(
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
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()

    return [dict(row) for row in rows]


@app.get("/matches/{match_id}")
def get_match(match_id: int):
    connection = get_connection()
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
    connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Match not found")

    return dict(row)


@app.post("/bets")
def place_bet(payload: BetCreate):
    connection = get_connection()
    cursor = connection.cursor()

    match = cursor.execute(
        """
        SELECT id, status, player_1, player_2
        FROM matches
        WHERE id = ?
        """,
        (payload.match_id,),
    ).fetchone()

    if match is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Match not found")

    if match["status"] != "pending":
        connection.close()
        raise HTTPException(status_code=400, detail="Cannot place bet on non-pending match")

    if payload.selected_player not in [match["player_1"], match["player_2"]]:
        connection.close()
        raise HTTPException(status_code=400, detail="Selected player is not part of this match")

    cursor.execute(
        """
        INSERT INTO bets (
            match_id,
            selected_player,
            stake,
            odds_taken,
            status,
            profit_loss,
            settled_at
        )
        VALUES (?, ?, ?, ?, 'open', NULL, NULL)
        """,
        (
            payload.match_id,
            payload.selected_player,
            payload.stake,
            payload.odds_taken,
        ),
    )

    bet_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return {
        "message": "Bet placed successfully",
        "bet_id": bet_id,
    }


@app.get("/bets")
def list_bets():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT
            id,
            match_id,
            selected_player,
            stake,
            odds_taken,
            status,
            profit_loss,
            settled_at
        FROM bets
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()

    return [dict(row) for row in rows]


@app.post("/bets/{bet_id}/settle")
def settle_bet(bet_id: int, payload: BetSettlement):
    connection = get_connection()
    cursor = connection.cursor()

    bet = cursor.execute(
        """
        SELECT id, selected_player, stake, odds_taken, status
        FROM bets
        WHERE id = ?
        """,
        (bet_id,),
    ).fetchone()

    if bet is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Bet not found")

    if bet["status"] != "open":
        connection.close()
        raise HTTPException(status_code=400, detail="Bet is already settled")

    if payload.winner == bet["selected_player"]:
        profit_loss = round(bet["stake"] * (bet["odds_taken"] - 1), 2)
        status = "won"
    else:
        profit_loss = round(-bet["stake"], 2)
        status = "lost"

    cursor.execute(
        """
        UPDATE bets
        SET status = ?, profit_loss = ?, settled_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, profit_loss, bet_id),
    )

    connection.commit()
    connection.close()

    return {
        "message": "Bet settled successfully",
        "bet_id": bet_id,
        "status": status,
        "profit_loss": profit_loss,
    }


@app.get("/bets/summary")
def bets_summary():
    connection = get_connection()

    summary = connection.execute(
        """
        SELECT
            COUNT(*) AS total_bets,
            COALESCE(SUM(stake), 0) AS total_staked,
            COALESCE(SUM(profit_loss), 0) AS total_profit_loss,
            COALESCE(AVG(profit_loss), 0) AS average_profit_loss
        FROM bets
        """
    ).fetchone()

    status_breakdown = connection.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM bets
        GROUP BY status
        ORDER BY status
        """
    ).fetchall()

    connection.close()

    return {
        "summary": dict(summary),
        "status_breakdown": [dict(row) for row in status_breakdown],
    }


@app.put("/matches/{match_id}/result")
def settle_match(match_id: int, payload: BetSettlement):
    connection = get_connection()
    cursor = connection.cursor()

    match = cursor.execute(
        """
        SELECT id, status, player_1, player_2
        FROM matches
        WHERE id = ?
        """,
        (match_id,),
    ).fetchone()

    if match is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Match not found")

    if payload.winner not in [match["player_1"], match["player_2"]]:
        connection.close()
        raise HTTPException(status_code=400, detail="Winner is not part of this match")

    cursor.execute(
        """
        UPDATE matches
        SET status = 'completed', winner = ?, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (payload.winner, match_id),
    )

    open_bets = cursor.execute(
        """
        SELECT id, selected_player, stake, odds_taken
        FROM bets
        WHERE match_id = ? AND status = 'open'
        """,
        (match_id,),
    ).fetchall()

    settled_bets = []

    for bet in open_bets:
        if bet["selected_player"] == payload.winner:
            status = "won"
            profit_loss = round(bet["stake"] * (bet["odds_taken"] - 1), 2)
        else:
            status = "lost"
            profit_loss = round(-bet["stake"], 2)

        cursor.execute(
            """
            UPDATE bets
            SET status = ?, profit_loss = ?, settled_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, profit_loss, bet["id"]),
        )

        settled_bets.append(
            {
                "bet_id": bet["id"],
                "status": status,
                "profit_loss": profit_loss,
            }
        )

    connection.commit()
    connection.close()

    return {
        "message": "Match settled successfully",
        "match_id": match_id,
        "winner": payload.winner,
        "settled_bets": settled_bets,
    }


@app.get("/matches/{match_id}/features")
def get_match_features(match_id: int):
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT
            id,
            match_id,
            player_name,
            surface,
            player_ranking,
            opponent_ranking,
            recent_wins,
            recent_losses,
            head_to_head_wins,
            head_to_head_losses,
            notes,
            created_at,
            updated_at
        FROM player_match_features
        WHERE match_id = ?
        ORDER BY id ASC
        """,
        (match_id,),
    ).fetchall()
    connection.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No feature rows found for this match")

    return [dict(row) for row in rows]


@app.put("/matches/{match_id}/features")
def update_match_features(match_id: int, payload: List[PlayerFeatureUpdate]):
    connection = get_connection()
    cursor = connection.cursor()

    existing_rows = cursor.execute(
        """
        SELECT id, player_name
        FROM player_match_features
        WHERE match_id = ?
        ORDER BY id ASC
        """,
        (match_id,),
    ).fetchall()

    if not existing_rows:
        connection.close()
        raise HTTPException(status_code=404, detail="No feature rows found for this match")

    if len(payload) != len(existing_rows):
        connection.close()
        raise HTTPException(
            status_code=400,
            detail="Payload length must match the number of player feature rows for this match",
        )

    updated_rows = []

    for row, feature_update in zip(existing_rows, payload):
        update_data = feature_update.dict()

        cursor.execute(
            """
            UPDATE player_match_features
            SET
                surface = ?,
                player_ranking = ?,
                opponent_ranking = ?,
                recent_wins = ?,
                recent_losses = ?,
                head_to_head_wins = ?,
                head_to_head_losses = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                update_data["surface"],
                update_data["player_ranking"],
                update_data["opponent_ranking"],
                update_data["recent_wins"],
                update_data["recent_losses"],
                update_data["head_to_head_wins"],
                update_data["head_to_head_losses"],
                update_data["notes"],
                row["id"],
            ),
        )

        updated_rows.append(
            {
                "feature_id": row["id"],
                "player_name": row["player_name"],
            }
        )

    connection.commit()
    connection.close()

    return {
        "message": "Match feature rows updated successfully",
        "match_id": match_id,
        "updated_rows": updated_rows,
    }


@app.get("/matches/{match_id}/features/status")
def get_match_feature_status(match_id: int):
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT
            player_name,
            surface,
            player_ranking,
            opponent_ranking,
            recent_wins,
            recent_losses,
            head_to_head_wins,
            head_to_head_losses
        FROM player_match_features
        WHERE match_id = ?
        ORDER BY id ASC
        """,
        (match_id,),
    ).fetchall()
    connection.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No feature rows found for this match")

    required_fields = [
        "surface",
        "player_ranking",
        "opponent_ranking",
        "recent_wins",
        "recent_losses",
        "head_to_head_wins",
        "head_to_head_losses",
    ]

    player_status = []

    for row in rows:
        missing_fields = [field for field in required_fields if row[field] is None]
        player_status.append(
            {
                "player_name": row["player_name"],
                "is_complete": len(missing_fields) == 0,
                "missing_fields": missing_fields,
            }
        )

    return {
        "match_id": match_id,
        "players": player_status,
        "match_ready": all(player["is_complete"] for player in player_status),
    }


@app.get("/features/player/{player_name}")
def get_player_feature_history(player_name: str):
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT
            pmf.id,
            pmf.match_id,
            pmf.player_name,
            pmf.surface,
            pmf.player_ranking,
            pmf.opponent_ranking,
            pmf.recent_wins,
            pmf.recent_losses,
            pmf.head_to_head_wins,
            pmf.head_to_head_losses,
            pmf.notes,
            pmf.created_at,
            pmf.updated_at,
            m.tournament,
            m.start_time,
            m.player_1,
            m.player_2,
            m.status,
            m.winner
        FROM player_match_features pmf
        JOIN matches m ON pmf.match_id = m.id
        WHERE pmf.player_name = ?
        ORDER BY pmf.match_id DESC
        """,
        (player_name,),
    ).fetchall()
    connection.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No feature history found for this player")

    return [dict(row) for row in rows]


@app.get("/matches/features/complete")
def get_complete_feature_matches():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT
            pmf.match_id,
            COUNT(*) AS player_rows,
            SUM(
                CASE
                    WHEN surface IS NOT NULL
                     AND player_ranking IS NOT NULL
                     AND opponent_ranking IS NOT NULL
                     AND recent_wins IS NOT NULL
                     AND recent_losses IS NOT NULL
                     AND head_to_head_wins IS NOT NULL
                     AND head_to_head_losses IS NOT NULL
                    THEN 1
                    ELSE 0
                END
            ) AS complete_rows
        FROM player_match_features pmf
        GROUP BY pmf.match_id
        HAVING player_rows = complete_rows
        ORDER BY pmf.match_id DESC
        """
    ).fetchall()

    complete_match_ids = [row["match_id"] for row in rows]

    if not complete_match_ids:
        connection.close()
        return []

    placeholders = ",".join("?" for _ in complete_match_ids)

    match_rows = connection.execute(
        f"""
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
        WHERE id IN ({placeholders})
        ORDER BY id DESC
        """,
        complete_match_ids,
    ).fetchall()

    connection.close()

    return [dict(row) for row in match_rows]


@app.get("/matches/{match_id}/score/{player_name}")
def get_player_feature_score(match_id: int, player_name: str):
    try:
        return calculate_player_score(match_id, player_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
