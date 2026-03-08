from apps.api.db.database import get_match_by_id
from apps.api.services.feature_scoring import calculate_player_score


def build_strategy_decision(match_id: int):
    match = get_match_by_id(match_id)

    if not match:
        return None

    player_1 = match["player_1"]
    player_2 = match["player_2"]

    player_1_score_data = calculate_player_score(match_id, player_1)
    player_2_score_data = calculate_player_score(match_id, player_2)

    player_1_score = player_1_score_data["score"]
    player_2_score = player_2_score_data["score"]

    if player_1_score > player_2_score:
        preferred_player = player_1
        score_difference = player_1_score - player_2_score
    elif player_2_score > player_1_score:
        preferred_player = player_2
        score_difference = player_2_score - player_1_score
    else:
        preferred_player = "no_edge"
        score_difference = 0

    return {
        "match_id": match_id,
        "match": {
            "player_1": player_1,
            "player_2": player_2,
            "tournament": match["tournament"],
            "start_time": match["start_time"],
            "odds_player_1": match["odds_player_1"],
            "odds_player_2": match["odds_player_2"],
        },
        "scores": {
            player_1: player_1_score_data,
            player_2: player_2_score_data,
        },
        "decision": {
            "preferred_player": preferred_player,
            "score_difference": score_difference,
        },
    }
