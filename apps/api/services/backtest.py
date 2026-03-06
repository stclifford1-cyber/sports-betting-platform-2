import sqlite3

DATABASE_PATH = "data/processed/app.db"
STARTING_BANKROLL = 1000.0


def run_backtest(selection_mode: str, flat_stake: float, player_name=None, tournament=None):
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        matches = connection.execute(
            """
            SELECT
                id,
                player_1,
                player_2,
                tournament,
                odds_player_1,
                odds_player_2,
                winner
            FROM matches
            WHERE status = 'completed'
            ORDER BY id ASC
            """
        ).fetchall()
    finally:
        connection.close()

    filtered_matches = []

    for match in matches:
        if player_name:
            if player_name not in [match["player_1"], match["player_2"]]:
                continue

        if tournament:
            if match["tournament"] != tournament:
                continue

        filtered_matches.append(match)

    total_bets = 0
    wins = 0
    losses = 0
    total_profit_loss = 0.0
    total_staked = 0.0
    total_odds = 0.0

    current_bankroll = STARTING_BANKROLL
    peak_bankroll = STARTING_BANKROLL
    max_drawdown = 0.0

    bet_results = []

    for match in filtered_matches:
        if selection_mode == "lower_odds":
            if match["odds_player_1"] <= match["odds_player_2"]:
                selection = match["player_1"]
                odds = match["odds_player_1"]
            else:
                selection = match["player_2"]
                odds = match["odds_player_2"]

        elif selection_mode == "higher_odds":
            if match["odds_player_1"] >= match["odds_player_2"]:
                selection = match["player_1"]
                odds = match["odds_player_1"]
            else:
                selection = match["player_2"]
                odds = match["odds_player_2"]
        else:
            continue

        total_bets += 1
        total_staked += flat_stake
        total_odds += odds

        if selection == match["winner"]:
            result = "won"
            wins += 1
            profit_loss = flat_stake * (odds - 1)
        else:
            result = "lost"
            losses += 1
            profit_loss = -flat_stake

        total_profit_loss += profit_loss
        current_bankroll += profit_loss

        if current_bankroll > peak_bankroll:
            peak_bankroll = current_bankroll

        drawdown = peak_bankroll - current_bankroll
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        bet_results.append(
            {
                "match_id": match["id"],
                "player_1": match["player_1"],
                "player_2": match["player_2"],
                "tournament": match["tournament"],
                "selection": selection,
                "winner": match["winner"],
                "odds": odds,
                "stake": flat_stake,
                "result": result,
                "profit_loss": profit_loss,
                "bankroll_after_bet": current_bankroll,
                "peak_bankroll_so_far": peak_bankroll,
                "drawdown_so_far": drawdown,
            }
        )

    roi = 0.0
    average_odds = 0.0
    strike_rate = 0.0

    if total_staked > 0:
        roi = total_profit_loss / total_staked

    if total_bets > 0:
        average_odds = total_odds / total_bets
        strike_rate = wins / total_bets

    return {
        "matches_scanned": len(matches),
        "matches_used": len(filtered_matches),
        "starting_bankroll": STARTING_BANKROLL,
        "ending_bankroll": current_bankroll,
        "peak_bankroll": peak_bankroll,
        "max_drawdown": max_drawdown,
        "total_bets": total_bets,
        "wins": wins,
        "losses": losses,
        "total_staked": total_staked,
        "total_profit_loss": total_profit_loss,
        "roi": roi,
        "average_odds": average_odds,
        "strike_rate": strike_rate,
        "bet_results": bet_results,
    }
