from fastapi import FastAPI

from apps.api.services.strategy_decision import build_strategy_decision
from apps.api.services.strategy_execution import (
    MAX_STAKE,
    build_candidate_bet,
    build_execution_label,
    build_strategy_preview,
    calculate_implied_profit,
    calculate_implied_return,
    calculate_stake,
    get_risk_level,
    get_stake_band,
    get_value_signal,
)


app = FastAPI(
    title="Sports Betting Strategy Development Platform"
)


@app.get("/")
def root():
    return {"status": "sports betting platform running"}


@app.get("/matches/{match_id}/decision")
def match_decision(match_id: int):
    return build_strategy_decision(match_id)


@app.get("/matches/{match_id}/execution")
def match_execution(match_id: int):
    return build_candidate_bet(match_id)


@app.get("/strategy/stake/{model_edge}")
def strategy_stake(model_edge: int):
    return {
        "model_edge": model_edge,
        "stake": calculate_stake(model_edge),
        "max_stake": MAX_STAKE,
        "stake_band": get_stake_band(model_edge),
    }


@app.get("/strategy/risk/{odds}")
def strategy_risk(odds: float):
    return {
        "odds": odds,
        "risk_level": get_risk_level(odds),
    }


@app.get("/strategy/payout/{stake}/{odds}")
def strategy_payout(stake: float, odds: float):
    return {
        "stake": stake,
        "odds": odds,
        "implied_return": calculate_implied_return(stake, odds),
        "implied_profit": calculate_implied_profit(stake, odds),
    }


@app.get("/strategy/label/{model_edge}/{odds}")
def strategy_label(model_edge: int, odds: float):
    stake_band = get_stake_band(model_edge)
    risk_level = get_risk_level(odds)

    return {
        "model_edge": model_edge,
        "odds": odds,
        "stake_band": stake_band,
        "risk_level": risk_level,
        "execution_label": build_execution_label(stake_band, risk_level),
    }


@app.get("/strategy/value/{model_edge}/{odds}")
def strategy_value(model_edge: int, odds: float):
    return {
        "model_edge": model_edge,
        "odds": odds,
        "value_signal": get_value_signal(model_edge, odds),
    }


@app.get("/strategy/preview/{model_edge}/{odds}")
def strategy_preview(model_edge: int, odds: float):
    return build_strategy_preview(model_edge, odds)
