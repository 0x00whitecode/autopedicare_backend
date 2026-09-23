from pydantic import BaseModel, Field


class RiskAssessmentRequest(BaseModel):
    vehicle_age_years: int | None = Field(default=None, ge=0)
    maintenance_score: int | None = Field(default=None, ge=0, le=100)
    accident_count: int | None = Field(default=None, ge=0)
    usage_hours_per_week: int | None = Field(default=None, ge=0)
    region_risk_index: int | None = Field(default=None, ge=0, le=100)


class RiskAssessmentResponse(BaseModel):
    risk_score: float
    risk_level: str
    summary: str
    recommendations: list[str]
