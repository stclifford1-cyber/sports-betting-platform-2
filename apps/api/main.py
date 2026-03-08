from fastapi import FastAPI, HTTPException

from apps.api.services.feature_scoring import calculate_player_score
from apps.api.services.strategy_decision import build_strategy_decision

app = FastAPI(title="Sports Betting Strategy Development Platform")


@app.get("/")
def root():
    return {"status": "sports betting platform running"}


@app.get("/matches/{match_id}/score/{player_name}")
def get_player_score(match_id: int, player_name: str):
    result = calculate_player_score(match_id, player_name)

    if result is None:
        raise HTTPException(status_code=404, detail="Score data not found")

    return result


@app.get("/matches/{match_id}/decision")
def get_strategy_decision(match_id: int):
    result = build_strategy_decision(match_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Match not found")

    return result
