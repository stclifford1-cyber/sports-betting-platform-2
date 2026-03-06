import sqlite3

DATABASE_PATH = "data/processed/app.db"
STARTING_BANKROLL = 1000.0


def get_bankroll_summary():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT id, profit_loss, settled_at
            FROM bets
            WHERE profit_loss IS NOT NULL
            ORDER BY settled_at ASC, id ASC
            """
        ).fetchall()
    finally:
        connection.close()

    total_profit_loss = 0.0
    current_bankroll = STARTING_BANKROLL
    peak_bankroll = STARTING_BANKROLL
    max_drawdown = 0.0

    bankroll_progression = []

    for row in rows:
        profit_loss = float(row["profit_loss"])
        total_profit_loss += profit_loss
        current_bankroll += profit_loss

        if current_bankroll > peak_bankroll:
            peak_bankroll = current_bankroll

        drawdown = peak_bankroll - current_bankroll
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        bankroll_progression.append({
            "bet_id": row["id"],
            "profit_loss": profit_loss,
            "bankroll_after_bet": current_bankroll
        })

    return {
        "starting_bankroll": STARTING_BANKROLL,
        "settled_bets_count": len(rows),
        "total_profit_loss": total_profit_loss,
        "current_bankroll": current_bankroll,
        "peak_bankroll": peak_bankroll,
        "drawdown": max_drawdown,
        "bankroll_progression": bankroll_progression
    }
