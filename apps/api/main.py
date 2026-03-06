from fastapi import FastAPI
from pydantic import BaseModel

from apps.api.db.database import (
    create_match,
    create_slate,
    get_strategy_experiment,
    init_db,
    list_strategy_experiments,
    record_match_result,
)
from apps.api.models.strategy import GridExperimentRequest, SimpleStrategyRequest
from apps.api.services.backtest import run_backtest
from apps.api.services.bankroll import get_bankroll_summary
from apps.api.services.strategy_runner import run_strategy_grid

app = FastAPI(title="Sports Betting Strategy Development Platform")


class SlateRequest(BaseModel):
    source: str


class MatchRequest(BaseModel):
    slate_id: int
    player_1: str
    player_2: str
    tournament: str
    start_time: str
    odds_player_1: float
    odds_player_2: float


class MatchResultRequest(BaseModel):
    winner: str


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"status": "sports betting platform running"}


@app.get("/info")
def info():
    return {
        "project": "Sports Betting Strategy Development Platform",
        "focus": "tennis",
        "stage": "strategy experiments",
    }


@app.post("/slate")
def post_slate(request: SlateRequest):
    return create_slate(request.source)


@app.post("/matches")
def post_match(request: MatchRequest):
    return create_match(
        slate_id=request.slate_id,
        player_1=request.player_1,
        player_2=request.player_2,
        tournament=request.tournament,
        start_time=request.start_time,
        odds_player_1=request.odds_player_1,
        odds_player_2=request.odds_player_2,
    )


@app.post("/matches/{match_id}/result")
def post_match_result(match_id: int, request: MatchResultRequest):
    return record_match_result(match_id, request.winner)


@app.get("/bankroll")
def bankroll():
    return get_bankroll_summary()


@app.post("/strategies/backtest")
def strategies_backtest(request: SimpleStrategyRequest):
    return run_backtest(
        selection_mode=request.selection_mode,
        flat_stake=request.flat_stake,
        player_name=request.player_name,
        tournament=request.tournament,
    )


@app.post("/strategies/grid")
def strategies_grid(request: GridExperimentRequest):
    return run_strategy_grid(request)


@app.get("/strategies/experiments")
def strategies_experiments():
    return list_strategy_experiments()


@app.get("/strategies/experiments/{experiment_id}")
def strategies_experiment_detail(experiment_id: int):
    return get_strategy_experiment(experiment_id)
