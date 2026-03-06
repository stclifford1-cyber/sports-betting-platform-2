from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator


ALLOWED_SELECTION_MODES = {"lower_odds", "higher_odds"}


class SimpleStrategyRequest(BaseModel):
    name: str = "simple_strategy"
    selection_mode: str
    flat_stake: float
    player_name: Optional[str] = None
    tournament: Optional[str] = None

    @validator("selection_mode")
    def validate_selection_mode(cls, value: str) -> str:
        if value not in ALLOWED_SELECTION_MODES:
            raise ValueError("selection_mode must be 'lower_odds' or 'higher_odds'")
        return value

    @validator("flat_stake")
    def validate_flat_stake(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("flat_stake must be positive")
        return value

    @validator("player_name", "tournament", pre=True)
    def normalise_optional_strings(cls, value):
        if value is None:
            return value
        value = value.strip()
        return value or None


class GridExperimentRequest(BaseModel):
    selection_modes: List[str]
    flat_stakes: List[float]
    player_name: Optional[str] = None
    tournament: Optional[str] = None
    top_n: Optional[int] = None

    @validator("selection_modes")
    def validate_selection_modes_not_empty(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("selection_modes must not be empty")
        return value

    @validator("selection_modes", each_item=True)
    def validate_selection_modes_values(cls, value: str) -> str:
        if value not in ALLOWED_SELECTION_MODES:
            raise ValueError("each selection_mode must be 'lower_odds' or 'higher_odds'")
        return value

    @validator("flat_stakes")
    def validate_flat_stakes_not_empty(cls, value: List[float]) -> List[float]:
        if not value:
            raise ValueError("flat_stakes must not be empty")
        return value

    @validator("flat_stakes", each_item=True)
    def validate_flat_stakes_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("each flat_stake must be positive")
        return value

    @validator("top_n")
    def validate_top_n(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("top_n must be positive when provided")
        return value

    @validator("player_name", "tournament", pre=True)
    def normalise_optional_strings(cls, value):
        if value is None:
            return value
        value = value.strip()
        return value or None


class StrategyExperimentListItem(BaseModel):
    experiment_id: int
    created_at: str
    experiment_request: Dict[str, Any]
    summary: Dict[str, Any]
    best_result: Optional[Dict[str, Any]] = None


class StrategyExperimentDetail(BaseModel):
    experiment_id: int
    created_at: str
    experiment_request: Dict[str, Any]
    ranking_method: Dict[str, Any]
    summary: Dict[str, Any]
    best_result: Optional[Dict[str, Any]] = None
    results: List[Dict[str, Any]]
