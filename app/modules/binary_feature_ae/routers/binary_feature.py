from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiExplainRuleRequest,
    ApiBinaryFeatureAiResponse,
)
from app.modules.binary_feature_ae.models.triage import (
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeatureCalculateResponse,
)
from app.modules.binary_feature_ae.service.ai_orchestrator import (
    explain_focused_rule_ai,
)
from app.modules.binary_feature_ae.service.binary_calc import (
    calculate_binary_feature_ae,
)

router = APIRouter()


@router.post(
    "/api/binary-feature-ae/calculate",
    response_model=ApiBinaryFeatureCalculateResponse,
)
def binary_feature_calculate(
    params: ApiBinaryFeatureCalculateRequest,
) -> ApiBinaryFeatureCalculateResponse:
    try:
        return calculate_binary_feature_ae(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/api/binary-feature-ae/ai/explain-rule",
    response_model=ApiBinaryFeatureAiResponse,
)
def binary_feature_explain_rule(
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> ApiBinaryFeatureAiResponse:
    try:
        return explain_focused_rule_ai(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/api/binary-feature-ae/ai/explain-focused-rule",
    response_model=ApiBinaryFeatureAiResponse,
)
def binary_feature_explain_focused_rule(
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> ApiBinaryFeatureAiResponse:
    try:
        return explain_focused_rule_ai(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
