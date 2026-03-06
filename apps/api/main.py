from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from apps.api.db.database import init_db, get_connection
from apps.api.services.bankroll import get_bankroll_summary
from apps.api.services.backtest import run_backtest
from apps.api.models.strategy import StrategyRequest


app = FastAPI(title="Sports Betting Strategy Development Platform")


class MatchEntry(BaseModel):
    player_1: str = Field(min_length=1)
    player_2: str = Field(min_length=1)
    tournament: str = Field(min_length=1)
    start_time: str
    odds_player_1: float = Field(gt=0)
    odds_player_2: float = Field(gt=0)


class DailySlate(BaseModel):
    source: str = Field(min_length=1)
    matches: List[MatchEntry] = Field(min_length=1)


class MatchResultUpdate(BaseModel):
    winner: str = Field(min_length=1)


class BetCreate(BaseModel):
    match_id: int
    selection: str = Field(min_length=1)
    odds: float = Field(gt=0)
    stake: float = Field(gt=0)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "sports betting platform running"}


@app.get("/info")
def info():
    return {
        "project": "Sports Betting Strategy Development Platform",
        "focus": "tennis",
        "stage": "strategy research"
    }


@app.get("/bankroll")
def bankroll():
    return get_bankroll_summary()


@app.post("/strategies/backtest")
def backtest_strategy(strategy: StrategyRequest):
    return run_backtest(
        strategy.selection_mode,
        strategy.flat_stake,
        strategy.player_name,
        strategy.tournament
    )


@app.post("/slate")
def create_slate(slate: DailySlate):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO slates (source, created_at)
        VALUES (?, ?)
        """,
        (
            slate.source,
            datetime.utcnow().isoformat()
        )
    )

    slate_id = cursor.lastrowid

    for match in slate.matches:
        cursor.execute(
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
                match.player_1,
                match.player_2,
                match.tournament,
                match.start_time,
                match.odds_player_1,
                match.odds_player_2
            )
        )

    connection.commit()
    connection.close()

    return {
        "message": "Slate stored in database",
        "slate_id": slate_id,
        "match_count": len(slate.matches)
    }


@app.get("/slates")
def list_slates():
    connection = get_connection()

    rows = connection.execute(
        "SELECT id, source, created_at FROM slates ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


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


@app.get("/matches/status/{status}")
def get_matches_by_status(status: str):
    if status not in ["pending", "completed"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be pending or completed"
        )

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
        WHERE status = ?
        ORDER BY id DESC
        """,
        (status,)
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


@app.get("/matches/player/{player_name}")
def get_matches_by_player(player_name: str):
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
        WHERE player_1 = ? OR player_2 = ?
        ORDER BY id DESC
        """,
        (player_name, player_name)
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


@app.post("/matches/{match_id}/result")
def record_match_result(match_id: int, result: MatchResultUpdate):
    connection = get_connection()

    match = connection.execute(
        """
        SELECT id, player_1, player_2
        FROM matches
        WHERE id = ?
        """,
        (match_id,)
    ).fetchone()

    if match is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Match not found")

    if result.winner not in [match["player_1"], match["player_2"]]:
        connection.close()
        raise HTTPException(
            status_code=400,
            detail="Winner must match player_1 or player_2"
        )

    completed_at = datetime.utcnow().isoformat()

    connection.execute(
        """
        UPDATE matches
        SET status = ?, winner = ?, completed_at = ?
        WHERE id = ?
        """,
        ("completed", result.winner, completed_at, match_id)
    )

    open_bets = connection.execute(
        """
        SELECT id, selection, odds, stake
        FROM bets
        WHERE match_id = ? AND status = 'open'
        """,
        (match_id,)
    ).fetchall()

    for bet in open_bets:
        if bet["selection"] == result.winner:
            status = "won"
            profit_loss = bet["stake"] * (bet["odds"] - 1)
        else:
            status = "lost"
            profit_loss = -bet["stake"]

        connection.execute(
            """
            UPDATE bets
            SET status = ?, profit_loss = ?, settled_at = ?
            WHERE id = ?
            """,
            (status, profit_loss, completed_at, bet["id"])
        )

    connection.commit()
    connection.close()

    return {"message": "Match result recorded and related bets settled"}


@app.post("/bets")
def create_bet(bet: BetCreate):
    connection = get_connection()

    match = connection.execute(
        """
        SELECT id, player_1, player_2
        FROM matches
        WHERE id = ?
        """,
        (bet.match_id,)
    ).fetchone()

    if match is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Match not found")

    if bet.selection not in [match["player_1"], match["player_2"]]:
        connection.close()
        raise HTTPException(
            status_code=400,
            detail="Selection must match player_1 or player_2"
        )

    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO bets (
            match_id,
            selection,
            odds,
            stake,
            status,
            profit_loss,
            placed_at,
            settled_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bet.match_id,
            bet.selection,
            bet.odds,
            bet.stake,
            "open",
            None,
            datetime.utcnow().isoformat(),
            None
        )
    )

    bet_id = cursor.lastrowid
    connection.commit()

    created_bet = connection.execute(
        """
        SELECT
            id,
            match_id,
            selection,
            odds,
            stake,
            status,
            profit_loss,
            placed_at,
            settled_at
        FROM bets
        WHERE id = ?
        """,
        (bet_id,)
    ).fetchone()

    connection.close()

    return {
        "message": "Bet recorded",
        "bet": dict(created_bet)
    }


@app.get("/bets")
def list_bets():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            match_id,
            selection,
            odds,
            stake,
            status,
            profit_loss,
            placed_at,
            settled_at
        FROM bets
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


@app.get("/bets/summary")
def bets_summary():
    connection = get_connection()

    summary = connection.execute(
        """
        SELECT
            COUNT(*) AS total_bets,
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_bets,
            SUM(CASE WHEN status IN ('won', 'lost') THEN 1 ELSE 0 END) AS settled_bets,
            SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) AS won_bets,
            SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) AS lost_bets,
            COALESCE(SUM(stake), 0) AS total_stake,
            COALESCE(SUM(CASE WHEN status IN ('won', 'lost') THEN stake ELSE 0 END), 0) AS settled_stake,
            COALESCE(SUM(profit_loss), 0) AS total_profit_loss
        FROM bets
        """
    ).fetchone()

    connection.close()

    return dict(summary)
