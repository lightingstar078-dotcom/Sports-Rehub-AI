from pydantic import BaseModel, Field
from typing import Literal

class AthleteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=5, le=100)
    sport: str = Field(min_length=1, max_length=120)
    injury: str = Field(min_length=1, max_length=200)
    injury_side: str = Field(default="N/A", max_length=30)

class PainPsychology(BaseModel):
    pain: float = Field(ge=0, le=10)
    psychological_readiness: float = Field(ge=0, le=100)

class MLPredictRequest(BaseModel):
    movement_quality: float = Field(ge=0, le=100)
    symmetry: float = Field(ge=0, le=100)
    rom: float = Field(ge=0, le=100)
    stability: float = Field(ge=0, le=100)
    landing_control: float = Field(ge=0, le=100)
    movement_consistency: float = Field(ge=0, le=100)
    pain: float = Field(ge=0, le=10)
    psychological_readiness: float = Field(ge=0, le=100)
    recovery_trend: float = Field(default=50, ge=0, le=100)
