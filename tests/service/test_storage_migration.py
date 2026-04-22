from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.core.models.dataset_config import ModuleId, PerformanceType
from app.core.service.dataset_config import get_config_file_path
from app.core.service.storage import normalize_stored_file_path


def _build_saved_config_payload(*, config_id: str, file_path: str) -> dict[str, object]:
    return {
        "id": config_id,
        "dataset_name": "configured-ae",
        "performance_type": PerformanceType.MORTALITY_AE.value,
        "file_path": file_path,
        "module_id": ModuleId.MORTALITY_AE.value,
        "module_config": {
            "policy_number_column": "application_number",
            "face_amount_column": None,
            "mac_column": "MAC",
            "mec_column": "MEC",
            "man_column": "MAN",
            "men_column": "MEN",
            "moc_column": "MOC",
            "cola_m1_column": None,
        },
        "created_date": datetime(2025, 1, 1).isoformat(),
    }


def _write_saved_config_tree(
    *,
    storage_root: Path,
    config_id: str,
    stored_file_path: str,
    filename: str = "saved.csv",
) -> None:
    file_path = storage_root / "files" / config_id / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        "application_number,MEC,MAC,MAN,MEN,MOC,age\n"
        "A1,1,1,100,100,1,30\n"
        "A2,1,2,200,100,1,50\n",
        encoding="utf-8",
    )
    (storage_root / "dataset_configs.json").write_text(
        json.dumps(
            [_build_saved_config_payload(config_id=config_id, file_path=stored_file_path)],
            indent=2,
        ),
        encoding="utf-8",
    )


def test_startup_creates_canonical_storage_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))

    with TestClient(create_app()):
        pass

    assert (tmp_path / ".insight-hub").is_dir()


def test_startup_normalizes_managed_canonical_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    canonical_root = tmp_path / ".insight-hub"
    config_id = "canonical-config"
    _write_saved_config_tree(
        storage_root=canonical_root,
        config_id=config_id,
        stored_file_path=".insight-hub/files/canonical-config/saved.csv",
    )

    with TestClient(create_app()) as client:
        response = client.get(f"/api/dataset-configs/{config_id}/schema")
        assert response.status_code == 200

    assert canonical_root.is_dir()
    assert (canonical_root / "files" / config_id / "saved.csv").exists()

    payload = json.loads(
        (canonical_root / "dataset_configs.json").read_text(encoding="utf-8")
    )
    assert payload[0]["file_path"] == "saved.csv"


def test_normalize_stored_file_path_handles_canonical_variants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    config_id = "path-config"

    canonical_absolute = str(
        tmp_path / ".insight-hub" / "files" / config_id / "current.csv"
    )
    outside_path = str(tmp_path / "outside.csv")

    assert normalize_stored_file_path(config_id, "plain.csv") == (
        "plain.csv",
        False,
    )
    assert normalize_stored_file_path(config_id, canonical_absolute) == (
        "current.csv",
        True,
    )
    assert normalize_stored_file_path(
        config_id,
        ".insight-hub/files/path-config/current.csv",
    ) == ("current.csv", True)
    assert normalize_stored_file_path(config_id, outside_path) == (
        outside_path,
        False,
    )


def test_get_config_file_path_resolves_through_storage_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    canonical_root = tmp_path / ".insight-hub"
    config_id = "resolved-config"
    _write_saved_config_tree(
        storage_root=canonical_root,
        config_id=config_id,
        stored_file_path=".insight-hub/files/resolved-config/saved.csv",
    )

    file_path = get_config_file_path(config_id)

    assert file_path == canonical_root / "files" / config_id / "saved.csv"


def test_invalid_legacy_binary_config_does_not_blank_config_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    canonical_root = tmp_path / ".insight-hub"
    valid_config_id = "valid-config"
    invalid_config_id = "legacy-binary-config"
    _write_saved_config_tree(
        storage_root=canonical_root,
        config_id=valid_config_id,
        stored_file_path=".insight-hub/files/valid-config/saved.csv",
    )

    configs_file = canonical_root / "dataset_configs.json"
    payload = json.loads(configs_file.read_text(encoding="utf-8"))
    payload.append(
        {
            "id": invalid_config_id,
            "dataset_name": "legacy-binary",
            "performance_type": PerformanceType.BINARY_FEATURE_AE.value,
            "file_path": "legacy.csv",
            "module_id": ModuleId.BINARY_FEATURE_AE.value,
            "module_config": {
                "rule": "rule",
                "RuleName": "RuleName",
                "first_date": "first_date",
                "category": "category",
                "hit_count": "hit_count",
            },
            "created_date": datetime(2025, 1, 2).isoformat(),
        }
    )
    configs_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with TestClient(create_app()) as client:
        response = client.get("/api/dataset-configs")
        assert response.status_code == 200
        body = response.json()

    config_ids = [item["id"] for item in body["configs"]]
    assert valid_config_id in config_ids
    assert invalid_config_id not in config_ids


def test_legacy_binary_config_with_man_sum_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    canonical_root = tmp_path / ".insight-hub"
    valid_config_id = "valid-config"
    legacy_config_id = "legacy-man-sum-config"
    _write_saved_config_tree(
        storage_root=canonical_root,
        config_id=valid_config_id,
        stored_file_path=".insight-hub/files/valid-config/saved.csv",
    )

    configs_file = canonical_root / "dataset_configs.json"
    payload = json.loads(configs_file.read_text(encoding="utf-8"))
    payload.append(
        {
            "id": legacy_config_id,
            "dataset_name": "legacy-binary",
            "performance_type": PerformanceType.BINARY_FEATURE_AE.value,
            "file_path": "legacy.csv",
            "module_id": ModuleId.BINARY_FEATURE_AE.value,
            "module_config": {
                "rule": "rule",
                "RuleName": "RuleName",
                "first_date": "first_date",
                "category": "category",
                "hit_count": "hit_count",
                "hit_rate": "hit_rate",
                "claim_count": "claim_count",
                "claim_amount": "claim_amount",
                "man_sum": "man_sum",
                "mec_sum": "mec_sum",
                "ae_ratio_count": "ae_ratio_count",
                "ci_lower_95_count": "ci_lower_95_count",
                "ci_upper_95_count": "ci_upper_95_count",
                "ci_lower_90_count": "ci_lower_90_count",
                "ci_upper_90_count": "ci_upper_90_count",
                "ci_lower_80_count": "ci_lower_80_count",
                "ci_upper_80_count": "ci_upper_80_count",
                "cola_cancer_pct_count": "cola_cancer_pct_count",
                "cola_heart_pct_count": "cola_heart_pct_count",
                "cola_nervous_system_pct_count": "cola_nervous_system_pct_count",
                "cola_non_natural_pct_count": "cola_non_natural_pct_count",
                "cola_other_medical_pct_count": "cola_other_medical_pct_count",
                "cola_respiratory_pct_count": "cola_respiratory_pct_count",
                "cola_others_pct_count": "cola_others_pct_count",
                "ae_ratio_amount": "ae_ratio_amount",
                "ci_lower_95_amount": "ci_lower_95_amount",
                "ci_upper_95_amount": "ci_upper_95_amount",
                "ci_lower_90_amount": "ci_lower_90_amount",
                "ci_upper_90_amount": "ci_upper_90_amount",
                "ci_lower_80_amount": "ci_lower_80_amount",
                "ci_upper_80_amount": "ci_upper_80_amount",
                "cola_cancer_pct_amount": "cola_cancer_pct_amount",
                "cola_heart_pct_amount": "cola_heart_pct_amount",
                "cola_nervous_system_pct_amount": "cola_nervous_system_pct_amount",
                "cola_non_natural_pct_amount": "cola_non_natural_pct_amount",
                "cola_other_medical_pct_amount": "cola_other_medical_pct_amount",
                "cola_respiratory_pct_amount": "cola_respiratory_pct_amount",
                "cola_others_pct_amount": "cola_others_pct_amount",
            },
            "created_date": datetime(2025, 1, 3).isoformat(),
        }
    )
    configs_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with TestClient(create_app()) as client:
        response = client.get("/api/dataset-configs")
        assert response.status_code == 200
        body = response.json()

    config_ids = [item["id"] for item in body["configs"]]
    assert valid_config_id in config_ids
    assert legacy_config_id not in config_ids
