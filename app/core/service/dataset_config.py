from __future__ import annotations

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from app.core.models.dataset_config import (
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiListDatasetConfigsResults,
)
from app.core.service.storage import (
    get_config_file_dir,
    get_configs_file,
    get_dataset_file_path,
    normalize_stored_file_path,
)

logger = logging.getLogger(__name__)


def save_uploaded_file(config_id: str, file_content: BinaryIO, filename: str) -> Path:
    """Save an uploaded file for a configuration."""
    config_dir = get_config_file_dir(config_id, create=True)
    file_path = config_dir / filename

    with file_path.open("wb") as handle:
        shutil.copyfileobj(file_content, handle)

    return file_path


def get_config_file_path(config_id: str) -> Path | None:
    """Get the file path for a configuration's saved file."""
    configs = _load_configs()
    config = next((c for c in configs if c.id == config_id), None)

    if not config:
        return None

    file_path = get_dataset_file_path(config_id, config.file_path)

    if file_path is not None and file_path.exists():
        return file_path
    return None


def get_dataset_config_with_file(config_id: str) -> tuple[ApiDatasetConfig, Path]:
    """Get a saved configuration and its stored file path."""
    config = get_dataset_config(config_id)
    if config is None:
        raise ValueError(f"Dataset config '{config_id}' not found")

    file_path = get_config_file_path(config_id)
    if file_path is None:
        raise ValueError(f"File for config '{config_id}' not found")

    return config, file_path


def _load_configs() -> list[ApiDatasetConfig]:
    """Load all dataset configurations from disk."""
    configs_file = get_configs_file()
    if not configs_file.exists():
        return []

    try:
        with configs_file.open(encoding="utf-8") as handle:
            data = json.load(handle)

        configs = []
        for item in data:
            payload = dict(item)
            try:
                payload["created_date"] = datetime.fromisoformat(payload["created_date"])
                configs.append(ApiDatasetConfig(**payload))
            except Exception as exc:
                logger.warning(
                    "Skipping invalid dataset config '%s' for module '%s': %s",
                    payload.get("id", "<unknown>"),
                    payload.get("module_id", "<unknown>"),
                    exc,
                )
        return configs
    except Exception as exc:
        logger.warning("Failed to load dataset configs from '%s': %s", configs_file, exc)
        return []


def _save_configs(configs: list[ApiDatasetConfig]) -> None:
    """Save all dataset configurations to disk."""
    configs_file = get_configs_file()

    data = []
    for config in configs:
        config_dict = config.model_dump()
        config_dict["created_date"] = config.created_date.isoformat()
        data.append(config_dict)

    with configs_file.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def list_dataset_configs() -> ApiListDatasetConfigsResults:
    """List all saved dataset configurations."""
    configs = _load_configs()
    configs.sort(key=lambda c: c.created_date, reverse=True)
    return ApiListDatasetConfigsResults(configs=configs)


def create_dataset_config(request: ApiCreateDatasetConfigRequest) -> ApiDatasetConfig:
    """Create a new dataset configuration."""
    configs = _load_configs()

    config_id = str(uuid.uuid4())
    stored_file_path, _ = normalize_stored_file_path(config_id, request.file_path)

    new_config = ApiDatasetConfig(
        id=config_id,
        dataset_name=request.dataset_name,
        performance_type=request.performance_type,
        file_path=stored_file_path,
        module_id=request.module_id,
        module_config=request.module_config,
        created_date=datetime.now(),
    )

    configs.append(new_config)
    _save_configs(configs)

    return new_config


def get_dataset_config(config_id: str) -> ApiDatasetConfig | None:
    """Get a specific dataset configuration by ID."""
    configs = _load_configs()
    for config in configs:
        if config.id == config_id:
            return config
    return None


def delete_dataset_config(config_id: str) -> bool:
    """Delete a dataset configuration by ID."""
    configs = _load_configs()
    original_count = len(configs)
    configs = [c for c in configs if c.id != config_id]

    if len(configs) < original_count:
        _save_configs(configs)

        try:
            config_dir = get_config_file_dir(config_id, create=False)
            if config_dir.exists():
                shutil.rmtree(config_dir)
        except Exception:
            pass

        return True
    return False
