from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List


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
        "stage": "validated ingestion API"
    }


@app.post("/slate")
def create_slate(slate: DailySlate):
    app_state["latest_slate"] = slate.model_dump()

    return {
        "message": "Daily slate accepted",
        "match_count": len(slate.matches),
        "source": slate.source
    }


@app.get("/slate")
def get_latest_slate():
    return {
        "latest_slate": app_state["latest_slate"]
    }
