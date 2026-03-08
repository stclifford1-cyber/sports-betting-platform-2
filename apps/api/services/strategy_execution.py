from apps.api.db.database import get_connection
from apps.api.services.strategy_decision import build_strategy_decision


STRATEGY_NAME = "score_difference_strategy_v1"
MAX_STAKE = 20.0


def calculate_stake(model_edge: int) -> float:
    if model_edge >= 5:
        return min(20.0, MAX_STAKE)
    if model_edge >= 3:
        return min(10.0, MAX_STAKE)
    return min(5.0, MAX_STAKE)


def get_stake_band(model_edge: int) -> str:
    if model_edge >= 5:
        return "high_edge"
    if model_edge >= 3:
        return "medium_edge"
    return "low_edge"


def calculate_implied_return(stake: float, odds: float) -> float:
    return round(stake * odds, 2)


def calculate_implied_profit(stake: float, odds: float) -> float:
    return round((stake * odds) - stake, 2)


def get_risk_level(odds: float) -> str:
    if odds >= 2.5:
        return "high_risk"
    if odds >= 1.8:
        return "medium_risk"
    return "low_risk"


def build_execution_label(stake_band: str, risk_level: str) -> str:
    return f"{stake_band}_{risk_level}"


def get_value_signal(model_edge: int, odds: float) -> str:
    if model_edge >= 5 and odds >= 2.0:
        return "strong_value"
    if model_edge >= 3 and odds >= 1.8:
        return "moderate_value"
    return "neutral_value"


def build_strategy_preview(model_edge: int, odds: float) -> dict:
    stake = calculate_stake(model_edge)
    stake_band = get_stake_band(model_edge)
    risk_level = get_risk_level(odds)

    return {
        "model_edge": model_edge,
        "odds": odds,
        "stake": stake,
        "max_stake": MAX_STAKE,
        "stake_band": stake_band,
        "risk_level": risk_level,
        "execution_label": build_execution_label(stake_band, risk_level),
        "value_signal": get_value_signal(model_edge, odds),
        "implied_return": calculate_implied_return(stake, odds),
        "implied_profit": calculate_implied_profit(stake, odds),
        "strategy": STRATEGY_NAME,
    }


def build_candidate_bet(match_id: int) -> dict:
    decision_output = build_strategy_decision(match_id)

    preferred_player = decision_output["decision"]["preferred_player"]
    model_edge = decision_output["decision"]["score_difference"]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, player_1, player_2, odds_player_1, odds_player_2
        FROM matches
        WHERE id = ?
        """,
        (match_id,),
    )
    row = cursor.fetchone()
    connection.close()

    if row is None:
        raise ValueError(f"Match {match_id} not found.")

    if preferred_player == row["player_1"]:
        selected_odds = row["odds_player_1"]
    elif preferred_player == row["player_2"]:
        selected_odds = row["odds_player_2"]
    else:
        raise ValueError(
            f"Preferred player '{preferred_player}' does not match players in match {match_id}."
        )

    preview = build_strategy_preview(model_edge, selected_odds)

    return {
        "match_id": match_id,
        "selection": preferred_player,
        **preview,
    }
