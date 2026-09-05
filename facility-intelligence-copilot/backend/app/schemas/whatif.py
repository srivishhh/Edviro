from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class WhatIfParameterChanges(BaseModel):
    """Hypothetical modifications to an asset's operating parameters."""
    model_config = ConfigDict(extra="ignore")

    temperature: float | None = Field(
        default=None,
        ge=-50.0,
        le=150.0,
        description="Simulated temperature in °C",
    )
    pressure: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Simulated refrigerant or duct pressure in bar",
    )
    airflow: float | None = Field(
        default=None,
        ge=0.0,
        le=50000.0,
        description="Simulated airflow (CFM or % rated flow)",
    )
    energy_kw: float | None = Field(
        default=None,
        ge=0.0,
        le=5000.0,
        description="Simulated electrical power demand in kW",
    )


class WhatIfSimulateRequest(BaseModel):
    """Request payload for What-If simulation."""
    model_config = ConfigDict(extra="ignore")

    asset_id: str | int = Field(
        ...,
        description="Target asset identifier (e.g. 'HVAC-007' or 7)",
    )
    changes: WhatIfParameterChanges = Field(
        default_factory=WhatIfParameterChanges,
        description="Hypothetical parameter adjustments",
    )
    scenario_preset: str | None = Field(
        default=None,
        max_length=64,
        description="Optional scenario preset name",
    )


class WhatIfParameterState(BaseModel):
    """Operational snapshot containing physical metrics, health, and operational risk."""
    model_config = ConfigDict(extra="ignore")

    temperature: float = Field(..., description="Temperature in °C")
    pressure: float = Field(..., description="Pressure in bar")
    airflow: float = Field(..., description="Airflow in CFM or %")
    energy_kw: float = Field(..., description="Power in kW")
    health: float = Field(..., ge=0.0, le=100.0, description="Asset health score 0-100")
    risk: float = Field(..., ge=0.0, le=100.0, description="Operational risk score 0-100")
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, or CRITICAL")


class WhatIfImpact(BaseModel):
    """Quantitative impact comparison between current and predicted states."""
    model_config = ConfigDict(extra="ignore")

    energy_change_kw: float = Field(..., description="Absolute change in kW (predicted - current)")
    energy_change_percent: float = Field(..., description="Percentage change in energy consumption")
    health_change: float = Field(..., description="Net change in asset health score")
    risk_change: float = Field(..., description="Net change in operational risk score")


class WhatIfSimulateResponse(BaseModel):
    """Full decision-support simulation result."""
    model_config = ConfigDict(extra="ignore")

    asset_id: str
    asset_name: str
    current: WhatIfParameterState
    predicted: WhatIfParameterState
    impact: WhatIfImpact
    assessment: str
    recommendations: list[str]
    explanation: str
    scenario_preset: str | None = None
    is_simulation: bool = True


class WhatIfPreset(BaseModel):
    """Definition of a scenario preset for quick What-If exploration."""
    id: str
    name: str
    description: str
    changes: WhatIfParameterChanges
    expected_outcome: str
