from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.core.models.dataset_config import (
    ApiBinaryFeatureAeModuleConfig,
    ApiMortalityAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ModuleId,
    PerformanceType,
)
from app.core.service.dataset_config import (
    create_dataset_config,
    get_config_file_path,
    get_dataset_config,
    save_uploaded_file,
)


def test_saved_configs_persist_across_app_startup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))

    request = ApiCreateDatasetConfigRequest(
        dataset_name="persisted-config",
        performance_type=PerformanceType.MORTALITY_AE,
        file_path="persisted.csv",
        module_id=ModuleId.MORTALITY_AE,
        module_config=ApiMortalityAeModuleConfig(
            policy_number_column="policy_number",
            face_amount_column=None,
            mac_column="MAC",
            mec_column="MEC",
            man_column="MAN",
            men_column="MEN",
            moc_column="MOC",
            cola_m1_column=None,
        ),
    )
    config = create_dataset_config(request)
    save_uploaded_file(
        config.id,
        BytesIO(
            b"policy_number,MEC,MAC,MAN,MEN,MOC,sex\n"
            b"P1,1,1,100,100,1,F\n"
        ),
        "persisted.csv",
    )

    with TestClient(create_app()) as client:
        response = client.get("/api/dataset-configs")
        assert response.status_code == 200
        assert response.json()["configs"][0]["id"] == config.id

    persisted = get_dataset_config(config.id)
    assert persisted is not None
    file_path = get_config_file_path(config.id)
    assert file_path is not None
    assert file_path.exists()
    assert (tmp_path / ".insight-hub").is_dir()


def test_binary_feature_configs_persist_with_widened_mapping_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))

    request = ApiCreateDatasetConfigRequest(
        dataset_name="binary-perspectives",
        performance_type=PerformanceType.BINARY_FEATURE_AE,
        file_path="binary.csv",
        module_id=ModuleId.BINARY_FEATURE_AE,
        module_config=ApiBinaryFeatureAeModuleConfig(
            rule="rule",
            RuleName="RuleName",
            first_date="first_date",
            category="category",
            hit_count="hit_count",
            hit_rate="hit_rate",
            claim_count="claim_count",
            claim_amount="claim_amount",
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
        ),
    )
    config = create_dataset_config(request)
    save_uploaded_file(
        config.id,
        BytesIO(
            b"rule,RuleName,first_date,category,hit_count,hit_rate,claim_count,claim_amount,mec_sum,"
            b"ae_ratio_count,ci_lower_95_count,ci_upper_95_count,ci_lower_90_count,ci_upper_90_count,"
            b"ci_lower_80_count,ci_upper_80_count,cola_cancer_pct_count,cola_heart_pct_count,"
            b"cola_nervous_system_pct_count,cola_non-natural_pct_count,cola_other_medical_pct_count,"
            b"cola_respiratory_pct_count,cola_others_pct_count,ae_ratio_amount,ci_lower_95_amount,"
            b"ci_upper_95_amount,ci_lower_90_amount,ci_upper_90_amount,ci_lower_80_amount,"
            b"ci_upper_80_amount,cola_cancer_pct_amount,cola_heart_pct_amount,"
            b"cola_nervous_system_pct_amount,cola_non-natural_pct_amount,"
            b"cola_other_medical_pct_amount,cola_respiratory_pct_amount,cola_others_pct_amount\n"
            b"R1,Rule One,2024-01-01,Cancer,10,0.1,2,1000,1.5,1.2,1.0,1.4,1.02,1.38,1.05,1.35,0.5,0.2,0.1,0.05,0.05,0.05,0.05,0.9,0.8,1.0,0.82,0.98,0.84,0.96,0.2,0.4,0.1,0.1,0.1,0.05,0.05\n"
        ),
        "binary.csv",
    )

    with TestClient(create_app()) as client:
        response = client.get("/api/dataset-configs")
        assert response.status_code == 200
        body = response.json()

    saved = next(item for item in body["configs"] if item["id"] == config.id)
    assert saved["module_config"]["claim_amount"] == "claim_amount"
    assert saved["module_config"]["ae_ratio_count"] == "ae_ratio_count"
    assert saved["module_config"]["ae_ratio_amount"] == "ae_ratio_amount"

    persisted = get_dataset_config(config.id)
    assert persisted is not None
