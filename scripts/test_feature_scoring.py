import sys
from pathlib import Path

# Ensure project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from apps.api.services.feature_scoring import calculate_player_score


def main():
    match_id = 6

    players = [
        "Carlos Alcaraz",
        "Jannik Sinner"
    ]

    results = []

    for player in players:
        result = calculate_player_score(match_id, player)
        results.append(result)

    print("Feature scoring results")
    print("-----------------------")

    for r in results:
        print(r)

    print("\nScore comparison")
    print("----------------")

    if results[0]["score"] > results[1]["score"]:
        print(f"{results[0]['player_name']} has the higher score")
    elif results[0]["score"] < results[1]["score"]:
        print(f"{results[1]['player_name']} has the higher score")
    else:
        print("Scores are equal")


if __name__ == "__main__":
    main()
