from typing import Optional
from pydantic import BaseModel, Field


class StrategyRequest(BaseModel):
    name: str = Field(min_length=1)
    selection_mode: str = Field(pattern="^(lower_odds|higher_odds)$")
    flat_stake: float = Field(gt=0)
    player_name: Optional[str] = None
    tournament: Optional[str] = None
