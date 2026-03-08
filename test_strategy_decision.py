from apps.api.services.strategy_decision import build_strategy_decision

match_id = 6

decision = build_strategy_decision(match_id)

print("Strategy Decision Output")
print("-----------------------")
print(decision)
