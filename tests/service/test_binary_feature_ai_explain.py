from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from app.core.models.dataset_config import (
    ApiBinaryFeatureAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ModuleId,
    PerformanceType,
)
from app.core.service.dataset_config import (
    create_dataset_config,
    save_uploaded_file,
)
from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiExplainRuleRequest,
    ApiBinaryFeatureAiSourceMode,
)
from app.modules.binary_feature_ae.models.triage import (
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeaturePerspective,
    ApiBinaryFeatureSignificance,
)
from app.modules.binary_feature_ae.service import ai_orchestrator
from app.modules.binary_feature_ae.service.ai_explain import (
    perform_binary_feature_explain_rule,
)
from app.modules.binary_feature_ae.service.ai_packets import (
    build_explain_focused_rule_packet,
)
from app.modules.binary_feature_ae.service.binary_calc import (
    calculate_binary_feature_ae,
)


def _sample_binary_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule": "R1",
                "RuleName": "Rule One",
                "first_date": "2024-01-01",
                "category": "Cancer",
                "hit_count": 100,
                "hit_rate": 0.12,
                "claim_count": 20,
                "claim_amount": 500000,
                "men_sum": 450000,
                "mec_sum": 18,
                "ae_ratio_count": 1.4,
                "ci_lower_95_count": 1.2,
                "ci_upper_95_count": 1.6,
                "ci_lower_90_count": 1.22,
                "ci_upper_90_count": 1.58,
                "ci_lower_80_count": 1.25,
                "ci_upper_80_count": 1.55,
                "ae_ratio_amount": 0.78,
                "ci_lower_95_amount": 0.6,
                "ci_upper_95_amount": 0.95,
                "ci_lower_90_amount": 0.62,
                "ci_upper_90_amount": 0.93,
                "ci_lower_80_amount": 0.65,
                "ci_upper_80_amount": 0.9,
                "cola_cancer_pct_count": 0.60,
                "cola_heart_pct_count": 0.20,
                "cola_nervous_system_pct_count": 0.05,
                "cola_non_natural_pct_count": 0.03,
                "cola_other_medical_pct_count": 0.04,
                "cola_respiratory_pct_count": 0.05,
                "cola_others_pct_count": 0.03,
                "cola_cancer_pct_amount": 0.20,
                "cola_heart_pct_amount": 0.45,
                "cola_nervous_system_pct_amount": 0.05,
                "cola_non_natural_pct_amount": 0.05,
                "cola_other_medical_pct_amount": 0.10,
                "cola_respiratory_pct_amount": 0.10,
                "cola_others_pct_amount": 0.05,
            },
            {
                "rule": "R2",
                "RuleName": "Rule Two",
                "first_date": "2024-02-01",
                "category": "Cardio",
                "hit_count": 10,
                "hit_rate": 0.02,
                "claim_count": 6,
                "claim_amount": 200000,
                "men_sum": 180000,
                "mec_sum": 8,
                "ae_ratio_count": 0.7,
                "ci_lower_95_count": 0.5,
                "ci_upper_95_count": 0.8,
                "ci_lower_90_count": 0.52,
                "ci_upper_90_count": 0.82,
                "ci_lower_80_count": 0.56,
                "ci_upper_80_count": 0.88,
                "ae_ratio_amount": 1.35,
                "ci_lower_95_amount": 1.1,
                "ci_upper_95_amount": 1.55,
                "ci_lower_90_amount": 1.12,
                "ci_upper_90_amount": 1.52,
                "ci_lower_80_amount": 1.15,
                "ci_upper_80_amount": 1.48,
                "cola_cancer_pct_count": 0.10,
                "cola_heart_pct_count": 0.55,
                "cola_nervous_system_pct_count": 0.05,
                "cola_non_natural_pct_count": 0.05,
                "cola_other_medical_pct_count": 0.10,
                "cola_respiratory_pct_count": 0.10,
                "cola_others_pct_count": 0.05,
                "cola_cancer_pct_amount": 0.50,
                "cola_heart_pct_amount": 0.20,
                "cola_nervous_system_pct_amount": 0.05,
                "cola_non_natural_pct_amount": 0.05,
                "cola_other_medical_pct_amount": 0.05,
                "cola_respiratory_pct_amount": 0.10,
                "cola_others_pct_amount": 0.05,
            },
            {
                "rule": "R3",
                "RuleName": "Rule Three",
                "first_date": "2024-03-01",
                "category": "Cancer",
                "hit_count": 5,
                "hit_rate": 0.01,
                "claim_count": 3,
                "claim_amount": 25000,
                "men_sum": 23000,
                "mec_sum": 4,
                "ae_ratio_count": 1.05,
                "ci_lower_95_count": 0.8,
                "ci_upper_95_count": 1.3,
                "ci_lower_90_count": 0.9,
                "ci_upper_90_count": 1.2,
                "ci_lower_80_count": 1.01,
                "ci_upper_80_count": 1.1,
                "ae_ratio_amount": 1.02,
                "ci_lower_95_amount": 0.9,
                "ci_upper_95_amount": 1.15,
                "ci_lower_90_amount": 0.94,
                "ci_upper_90_amount": 1.12,
                "ci_lower_80_amount": 0.97,
                "ci_upper_80_amount": 1.09,
                "cola_cancer_pct_count": 0.15,
                "cola_heart_pct_count": 0.15,
                "cola_nervous_system_pct_count": 0.20,
                "cola_non_natural_pct_count": 0.20,
                "cola_other_medical_pct_count": 0.10,
                "cola_respiratory_pct_count": 0.10,
                "cola_others_pct_count": 0.10,
                "cola_cancer_pct_amount": 0.15,
                "cola_heart_pct_amount": 0.15,
                "cola_nervous_system_pct_amount": 0.20,
                "cola_non_natural_pct_amount": 0.20,
                "cola_other_medical_pct_amount": 0.10,
                "cola_respiratory_pct_amount": 0.10,
                "cola_others_pct_amount": 0.10,
            },
        ]
    )


def _module_config() -> ApiBinaryFeatureAeModuleConfig:
    return ApiBinaryFeatureAeModuleConfig(
        rule="rule",
        RuleName="RuleName",
        first_date="first_date",
        category="category",
        hit_count="hit_count",
        hit_rate="hit_rate",
        claim_count="claim_count",
        claim_amount="claim_amount",
        men_sum="men_sum",
        mec_sum="mec_sum",
        ae_ratio_count="ae_ratio_count",
        ci_lower_95_count="ci_lower_95_count",
        ci_upper_95_count="ci_upper_95_count",
        ci_lower_90_count="ci_lower_90_count",
        ci_upper_90_count="ci_upper_90_count",
        ci_lower_80_count="ci_lower_80_count",
        ci_upper_80_count="ci_upper_80_count",
        cola_cancer_pct_count="cola_cancer_pct_count",
        cola_heart_pct_count="cola_heart_pct_count",
        cola_nervous_system_pct_count="cola_nervous_system_pct_count",
        cola_non_natural_pct_count="cola_non-natural_pct_count",
        cola_other_medical_pct_count="cola_other_medical_pct_count",
        cola_respiratory_pct_count="cola_respiratory_pct_count",
        cola_others_pct_count="cola_others_pct_count",
        ae_ratio_amount="ae_ratio_amount",
        ci_lower_95_amount="ci_lower_95_amount",
        ci_upper_95_amount="ci_upper_95_amount",
        ci_lower_90_amount="ci_lower_90_amount",
        ci_upper_90_amount="ci_upper_90_amount",
        ci_lower_80_amount="ci_lower_80_amount",
        ci_upper_80_amount="ci_upper_80_amount",
        cola_cancer_pct_amount="cola_cancer_pct_amount",
        cola_heart_pct_amount="cola_heart_pct_amount",
        cola_nervous_system_pct_amount="cola_nervous_system_pct_amount",
        cola_non_natural_pct_amount="cola_non-natural_pct_amount",
        cola_other_medical_pct_amount="cola_other_medical_pct_amount",
        cola_respiratory_pct_amount="cola_respiratory_pct_amount",
        cola_others_pct_amount="cola_others_pct_amount",
    )


def _create_saved_binary_config(tmp_path: Path) -> str:
    source_df = _sample_binary_df().rename(
        columns={
            "cola_non_natural_pct_count": "cola_non-natural_pct_count",
            "cola_non_natural_pct_amount": "cola_non-natural_pct_amount",
        }
    )
    csv_bytes = source_df.to_csv(index=False).encode("utf-8")

    request = ApiCreateDatasetConfigRequest(
        dataset_name="binary-ai-demo",
        performance_type=PerformanceType.BINARY_FEATURE_AE,
        file_path="binary.csv",
        module_id=ModuleId.BINARY_FEATURE_AE,
        module_config=_module_config(),
    )
    config = create_dataset_config(request)
    save_uploaded_file(config.id, BytesIO(csv_bytes), "binary.csv")
    return config.id


def _list_all_significance() -> list[ApiBinaryFeatureSignificance]:
    return [
        ApiBinaryFeatureSignificance.ELEVATED,
        ApiBinaryFeatureSignificance.UNCERTAIN,
        ApiBinaryFeatureSignificance.BELOW_EXPECTED,
    ]


def _lookup_row_id(*, config_id: str, rule: str) -> str:
    response = calculate_binary_feature_ae(
        params=ApiBinaryFeatureCalculateRequest(
            config_id=config_id,
            perspective=ApiBinaryFeaturePerspective.COUNT,
            categories=[],
            significance_values=_list_all_significance(),
            min_hit_count=0,
            min_claim_count=0,
        )
    )
    return next(row.row_id for row in response.rows if row.rule == rule)


def test_build_explain_focused_rule_packet_includes_fingerprint_and_baselines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    config_id = _create_saved_binary_config(tmp_path)
    row_id = _lookup_row_id(config_id=config_id, rule="R1")

    calculate_response = calculate_binary_feature_ae(
        params=ApiBinaryFeatureCalculateRequest(
            config_id=config_id,
            perspective=ApiBinaryFeaturePerspective.COUNT,
            categories=["Cancer"],
            significance_values=[
                ApiBinaryFeatureSignificance.ELEVATED,
                ApiBinaryFeatureSignificance.UNCERTAIN,
            ],
            min_hit_count=0,
            min_claim_count=0,
        )
    )

    packet = build_explain_focused_rule_packet(
        params=ApiBinaryFeatureAiExplainRuleRequest(
            config_id=config_id,
            perspective="count",
            ci_level="95",
            categories=["Cancer"],
            significance_values=["Elevated", "Uncertain"],
            search_text=None,
            min_hit_count=0,
            min_claim_count=0,
            row_id=row_id,
        )
    )

    assert packet.state_fingerprint == calculate_response.state_fingerprint
    assert packet.active_filters["categories"] == ["Cancer"]
    assert packet.visible_rule_count == 2
    assert packet.focused_row["rule"] == "R1"
    assert packet.baselines.impact_score_percentile > 0


def test_perform_binary_feature_explain_rule_rejects_hidden_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    config_id = _create_saved_binary_config(tmp_path)
    row_id = _lookup_row_id(config_id=config_id, rule="R1")

    with pytest.raises(ValueError, match="not visible"):
        perform_binary_feature_explain_rule(
            params=ApiBinaryFeatureAiExplainRuleRequest(
                config_id=config_id,
                perspective="count",
                ci_level="95",
                categories=["Cardio"],
                significance_values=["Elevated", "Uncertain", "Below Expected"],
                search_text=None,
                min_hit_count=0,
                min_claim_count=0,
                row_id=row_id,
            )
        )


def test_perform_binary_feature_explain_rule_uses_fallback_when_unconfigured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("INSIGHT_HUB_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("INSIGHT_HUB_LLM_API_KEY", raising=False)
    monkeypatch.delenv("INSIGHT_HUB_LLM_MODEL", raising=False)
    config_id = _create_saved_binary_config(tmp_path)
    row_id = _lookup_row_id(config_id=config_id, rule="R1")

    response = perform_binary_feature_explain_rule(
        params=ApiBinaryFeatureAiExplainRuleRequest(
            config_id=config_id,
            perspective="count",
            ci_level="95",
            categories=[],
            significance_values=["Elevated", "Uncertain", "Below Expected"],
            search_text=None,
            min_hit_count=0,
            min_claim_count=0,
            row_id=row_id,
        )
    )

    assert response.action_type == ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE
    assert response.source_mode == ApiBinaryFeatureAiSourceMode.FALLBACK
    assert response.summary_text
    assert response.key_findings
    assert response.reference_sources == []
    assert response.validation_notes


def test_perform_binary_feature_explain_rule_falls_back_on_bad_llm_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("INSIGHT_HUB_LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("INSIGHT_HUB_LLM_API_KEY", "test-key")
    monkeypatch.setenv("INSIGHT_HUB_LLM_MODEL", "test-model")
    config_id = _create_saved_binary_config(tmp_path)
    row_id = _lookup_row_id(config_id=config_id, rule="R1")

    monkeypatch.setattr(
        ai_orchestrator,
        "request_chat_completion_content",
        lambda **_kwargs: '{"summary_text":"missing required fields"}',
    )

    response = perform_binary_feature_explain_rule(
        params=ApiBinaryFeatureAiExplainRuleRequest(
            config_id=config_id,
            perspective="count",
            ci_level="95",
            categories=[],
            significance_values=["Elevated", "Uncertain", "Below Expected"],
            search_text=None,
            min_hit_count=0,
            min_claim_count=0,
            row_id=row_id,
        )
    )

    assert response.source_mode == ApiBinaryFeatureAiSourceMode.FALLBACK


def test_perform_binary_feature_explain_rule_accepts_valid_llm_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("INSIGHT_HUB_LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("INSIGHT_HUB_LLM_API_KEY", "test-key")
    monkeypatch.setenv("INSIGHT_HUB_LLM_MODEL", "test-model")
    config_id = _create_saved_binary_config(tmp_path)
    row_id = _lookup_row_id(config_id=config_id, rule="R1")
    packet = build_explain_focused_rule_packet(
        params=ApiBinaryFeatureAiExplainRuleRequest(
            config_id=config_id,
            perspective="count",
            ci_level="95",
            categories=[],
            significance_values=["Elevated", "Uncertain", "Below Expected"],
            search_text=None,
            min_hit_count=0,
            min_claim_count=0,
            row_id=row_id,
        )
    )

    def _mock_llm_response(**_kwargs: object) -> str:
        return json.dumps(
            {
                "action_type": "explain_focused_rule",
                "state_fingerprint": packet.state_fingerprint,
                "source_mode": "llm",
                "summary_text": (
                    "The selected rule is elevated relative to expected "
                    "and material within the visible set."
                ),
                "key_findings": [
                    "Count A/E is above expected within the current "
                    "filtered view."
                ],
                "caution_flags": [
                    "Interpret the rule in the context of concentration "
                    "by cause bucket."
                ],
                "next_review_steps": [
                    "Review recent claims contributing to the rule."
                ],
                "evidence_refs": [
                    {
                        "row_id": row_id,
                        "rule_label": str(packet.focused_row["rule_label"]),
                        "reason_type": "elevated_relative_to_expected",
                        "reason_label": "Elevated 95%",
                        "severity": "high",
                    }
                ],
                "used_reference_context": False,
                "reference_sources": [],
                "validation_notes": [],
            }
        )

    monkeypatch.setattr(
        ai_orchestrator,
        "request_chat_completion_content",
        _mock_llm_response,
    )

    response = perform_binary_feature_explain_rule(
        params=ApiBinaryFeatureAiExplainRuleRequest(
            config_id=config_id,
            perspective="count",
            ci_level="95",
            categories=[],
            significance_values=["Elevated", "Uncertain", "Below Expected"],
            search_text=None,
            min_hit_count=0,
            min_claim_count=0,
            row_id=row_id,
        )
    )

    assert response.action_type == ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE
    assert response.source_mode == ApiBinaryFeatureAiSourceMode.LLM
    assert response.state_fingerprint == packet.state_fingerprint
    assert response.key_findings == [
        "Count A/E is above expected within the current filtered view."
    ]
    assert response.validation_notes == []
