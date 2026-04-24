from __future__ import annotations

from fastapi.testclient import TestClient

from app import create_app
from app.modules.binary_feature_ae.routers import (
    binary_feature as binary_feature_router,
)


def test_binary_feature_ai_routes_share_the_same_response_shape(
    monkeypatch,
) -> None:
    def _mock_response(*, params):
        return {
            "action_type": "explain_focused_rule",
            "state_fingerprint": "fingerprint-1",
            "source_mode": "fallback",
            "summary_text": f"Summary for {params.row_id}",
            "key_findings": ["finding"],
            "caution_flags": ["caution"],
            "next_review_steps": ["step"],
            "evidence_refs": [],
            "used_reference_context": False,
            "reference_sources": [],
            "validation_notes": [
                "Deterministic fallback used because LLM output was "
                "unavailable or invalid."
            ],
        }

    monkeypatch.setattr(
        binary_feature_router,
        "explain_focused_rule_ai",
        _mock_response,
    )

    payload = {
        "config_id": "cfg-1",
        "perspective": "count",
        "ci_level": "95",
        "categories": [],
        "significance_values": ["Elevated", "Uncertain", "Below Expected"],
        "search_text": None,
        "min_hit_count": 0,
        "min_claim_count": 0,
        "row_id": "row-1",
    }

    with TestClient(create_app()) as client:
        legacy = client.post(
            "/api/binary-feature-ae/ai/explain-rule", json=payload
        )
        preferred = client.post(
            "/api/binary-feature-ae/ai/explain-focused-rule",
            json=payload,
        )

    assert legacy.status_code == 200
    assert preferred.status_code == 200
    assert legacy.json() == preferred.json()
