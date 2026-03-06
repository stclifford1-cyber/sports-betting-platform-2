from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from apps.api.db.database import init_db, get_connection


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
        "stage": "query endpoints"
    }


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
            odds_player_2
        FROM matches
        ORDER BY id DESC
        """
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
            odds_player_2
        FROM matches
        WHERE player_1 = ? OR player_2 = ?
        ORDER BY id DESC
        """,
        (player_name, player_name)
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]
