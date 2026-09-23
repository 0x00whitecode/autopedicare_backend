from fastapi import APIRouter

from app.ai.schemas import RiskAssessmentRequest, RiskAssessmentResponse

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/risk-assessment",
    response_model=RiskAssessmentResponse,
)
async def assess_risk(payload: RiskAssessmentRequest) -> RiskAssessmentResponse:
    score = 0.0
    factors = 0

    if payload.vehicle_age_years is not None:
        score += min(payload.vehicle_age_years * 1.5, 25)
        factors += 1

    if payload.maintenance_score is not None:
        score += (100 - payload.maintenance_score) * 0.35
        factors += 1

    if payload.accident_count is not None:
        score += payload.accident_count * 12
        factors += 1

    if payload.usage_hours_per_week is not None:
        score += min(payload.usage_hours_per_week * 1.1, 18)
        factors += 1

    if payload.region_risk_index is not None:
        score += payload.region_risk_index * 0.25
        factors += 1

    final_score = round(score / max(factors, 1), 2)

    if final_score < 30:
        level = "low"
        summary = "Asset risk is within acceptable operating limits."
        recommendations = [
            "Continue scheduled maintenance checks.",
            "Review vehicle logs during high-usage periods.",
        ]
    elif final_score < 60:
        level = "medium"
        summary = "Fleet activity suggests moderate risk and should be watched closely."
        recommendations = [
            "Increase preventive maintenance inspections.",
            "Review route and operating conditions for active vehicles.",
        ]
    else:
        level = "high"
        summary = "Risk score is elevated and requires intervention."
        recommendations = [
            "Escalate to maintenance review immediately.",
            "Validate recent repairs and safety checks before dispatch.",
            "Reduce exposure for high-risk operating conditions.",
        ]

    return RiskAssessmentResponse(
        risk_score=final_score,
        risk_level=level,
        summary=summary,
        recommendations=recommendations,
    )
