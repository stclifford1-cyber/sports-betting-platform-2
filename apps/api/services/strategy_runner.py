from apps.api.models.strategy import GridExperimentRequest
from apps.api.services.backtest import run_backtest
from apps.api.db.database import create_strategy_experiment


def clean_number(value):
    if isinstance(value, float):
        return round(value, 4)
    return value


def run_strategy_grid(request: GridExperimentRequest):
    ranked_results = []

    for selection_mode in request.selection_modes:
        for flat_stake in request.flat_stakes:
            backtest_result = run_backtest(
                selection_mode=selection_mode,
                flat_stake=flat_stake,
                player_name=request.player_name,
                tournament=request.tournament,
            )

            strategy_name = f"{selection_mode}_stake_{int(flat_stake) if float(flat_stake).is_integer() else flat_stake}"

            ranked_results.append(
                {
                    "strategy": strategy_name,
                    "selection_mode": selection_mode,
                    "stake": clean_number(flat_stake),
                    "matches_scanned": backtest_result["matches_scanned"],
                    "matches_used": backtest_result["matches_used"],
                    "total_bets": backtest_result["total_bets"],
                    "wins": backtest_result["wins"],
                    "losses": backtest_result["losses"],
                    "total_staked": clean_number(backtest_result["total_staked"]),
                    "total_profit_loss": clean_number(backtest_result["total_profit_loss"]),
                    "roi": clean_number(backtest_result["roi"]),
                    "average_odds": clean_number(backtest_result["average_odds"]),
                    "strike_rate": clean_number(backtest_result["strike_rate"]),
                    "starting_bankroll": clean_number(backtest_result["starting_bankroll"]),
                    "ending_bankroll": clean_number(backtest_result["ending_bankroll"]),
                    "peak_bankroll": clean_number(backtest_result["peak_bankroll"]),
                    "max_drawdown": clean_number(backtest_result["max_drawdown"]),
                }
            )

    ranked_results.sort(
        key=lambda item: (
            -item["roi"],
            -item["ending_bankroll"],
            item["max_drawdown"],
            item["stake"],
        )
    )

    for index, result in enumerate(ranked_results, start=1):
        result["rank"] = index

    full_results = ranked_results
    returned_results = full_results[:request.top_n] if request.top_n is not None else full_results

    best_result = full_results[0] if full_results else None
    worst_result = full_results[-1] if full_results else None

    positive_experiments = sum(1 for item in full_results if item["total_profit_loss"] > 0)
    negative_experiments = sum(1 for item in full_results if item["total_profit_loss"] < 0)
    break_even_experiments = sum(1 for item in full_results if item["total_profit_loss"] == 0)

    selection_mode_summary = []
    for mode in request.selection_modes:
        mode_results = [item for item in full_results if item["selection_mode"] == mode]

        if not mode_results:
            continue

        best_mode_result = mode_results[0]
        average_roi = sum(item["roi"] for item in mode_results) / len(mode_results)
        average_profit_loss = sum(item["total_profit_loss"] for item in mode_results) / len(mode_results)

        selection_mode_summary.append(
            {
                "selection_mode": mode,
                "experiments_run": len(mode_results),
                "best_strategy": best_mode_result["strategy"],
                "best_roi": clean_number(best_mode_result["roi"]),
                "average_roi": clean_number(average_roi),
                "average_profit_loss": clean_number(average_profit_loss),
            }
        )

    ranking_method = {
        "primary": "roi_desc",
        "tie_break_1": "ending_bankroll_desc",
        "tie_break_2": "max_drawdown_asc",
        "tie_break_3": "stake_asc",
    }

    summary = {
        "experiments_run": len(full_results),
        "results_returned": len(returned_results),
        "positive_experiments": positive_experiments,
        "negative_experiments": negative_experiments,
        "break_even_experiments": break_even_experiments,
        "best_strategy": best_result["strategy"] if best_result else None,
        "best_roi": best_result["roi"] if best_result else None,
        "worst_strategy": worst_result["strategy"] if worst_result else None,
        "worst_roi": worst_result["roi"] if worst_result else None,
        "selection_mode_summary": selection_mode_summary,
    }

    experiment_request = {
        "selection_modes": request.selection_modes,
        "flat_stakes": [clean_number(value) for value in request.flat_stakes],
        "player_name": request.player_name,
        "tournament": request.tournament,
        "top_n": request.top_n,
    }

    experiment_record = create_strategy_experiment(
        experiment_request=experiment_request,
        ranking_method=ranking_method,
        summary=summary,
        best_result=best_result,
        results=full_results,
    )

    return {
        "experiment_id": experiment_record["id"],
        "created_at": experiment_record["created_at"],
        "experiment_request": experiment_request,
        "ranking_method": ranking_method,
        "summary": summary,
        "best_result": best_result,
        "results": returned_results,
    }
