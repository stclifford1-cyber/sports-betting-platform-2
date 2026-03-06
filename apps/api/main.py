from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


app = FastAPI(title="Sports Betting Strategy Development Platform")


class MatchEntry(BaseModel):
    player_1: str
    player_2: str
    tournament: str
    start_time: str
    odds_player_1: float
    odds_player_2: float


class DailySlate(BaseModel):
    source: str
    matches: List[MatchEntry]


app_state = {
    "latest_slate": None
}


@app.get("/")
def root():
    return {"status": "sports betting platform running"}


@app.get("/info")
def info():
    return {
        "project": "Sports Betting Strategy Development Platform",
        "focus": "tennis",
        "stage": "initial ingestion API"
    }


@app.post("/slate")
def create_slate(slate: DailySlate):
    app_state["latest_slate"] = slate.model_dump()
    return {
        "message": "Daily slate received",
        "match_count": len(slate.matches),
        "source": slate.source
    }


@app.get("/slate")
def get_latest_slate():
    return {
        "latest_slate": app_state["latest_slate"]
    }
