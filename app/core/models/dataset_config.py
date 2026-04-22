from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModuleId(StrEnum):
    """Analysis module identifiers supported by the hub."""

    MORTALITY_AE = "mortality_ae"
    BINARY_FEATURE_AE = "binary_feature_ae"


class PerformanceType(StrEnum):
    """Types of performance analyses supported by the system."""

    MORTALITY_AE = "Mortality A/E Analysis"
    BINARY_FEATURE_AE = "Binary Feature Mortality A/E"


class ApiMortalityAeModuleConfig(BaseModel):
    """Column mappings for Mortality A/E Analysis."""

    model_config = ConfigDict(extra="forbid")

    policy_number_column: str | None = None
    face_amount_column: str | None = None
    mac_column: str
    mec_column: str
    man_column: str
    men_column: str
    moc_column: str | None = None
    cola_m1_column: str | None = None


class ApiBinaryFeatureAeModuleConfig(BaseModel):
    """Column mappings for the Binary Feature Mortality A/E module."""

    model_config = ConfigDict(extra="forbid")

    rule: str
    RuleName: str
    first_date: str
    category: str
    hit_count: str
    hit_rate: str
    claim_count: str
    claim_amount: str
    men_sum: str
    mec_sum: str
    ae_ratio_count: str
    ci_lower_95_count: str
    ci_upper_95_count: str
    ci_lower_90_count: str
    ci_upper_90_count: str
    ci_lower_80_count: str
    ci_upper_80_count: str
    cola_cancer_pct_count: str
    cola_heart_pct_count: str
    cola_nervous_system_pct_count: str
    cola_non_natural_pct_count: str
    cola_other_medical_pct_count: str
    cola_respiratory_pct_count: str
    cola_others_pct_count: str
    ae_ratio_amount: str
    ci_lower_95_amount: str
    ci_upper_95_amount: str
    ci_lower_90_amount: str
    ci_upper_90_amount: str
    ci_lower_80_amount: str
    ci_upper_80_amount: str
    cola_cancer_pct_amount: str
    cola_heart_pct_amount: str
    cola_nervous_system_pct_amount: str
    cola_non_natural_pct_amount: str
    cola_other_medical_pct_amount: str
    cola_respiratory_pct_amount: str
    cola_others_pct_amount: str


ApiModuleConfig = ApiMortalityAeModuleConfig | ApiBinaryFeatureAeModuleConfig


class ApiDatasetConfig(BaseModel):
    """A saved dataset configuration."""

    model_config = ConfigDict(extra="forbid")

    id: str
    dataset_name: str
    performance_type: PerformanceType
    file_path: str
    module_id: ModuleId
    module_config: ApiModuleConfig
    created_date: datetime

    @model_validator(mode="after")
    def _validate_module_config(self) -> "ApiDatasetConfig":
        if self.module_id == ModuleId.MORTALITY_AE and not isinstance(
            self.module_config, ApiMortalityAeModuleConfig
        ):
            raise ValueError("Mortality A/E configs require a mortality module_config")

        if self.module_id == ModuleId.BINARY_FEATURE_AE and not isinstance(
            self.module_config, ApiBinaryFeatureAeModuleConfig
        ):
            raise ValueError(
                "Binary Feature Mortality A/E configs require a binary feature module_config"
            )

        return self


class ApiCreateDatasetConfigRequest(BaseModel):
    """Request to create a new dataset configuration."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str = Field(min_length=1, max_length=200)
    performance_type: PerformanceType
    file_path: str
    module_id: ModuleId
    module_config: ApiModuleConfig

    @model_validator(mode="after")
    def _validate_module_config(self) -> "ApiCreateDatasetConfigRequest":
        if self.module_id == ModuleId.MORTALITY_AE and not isinstance(
            self.module_config, ApiMortalityAeModuleConfig
        ):
            raise ValueError("Mortality A/E configs require a mortality module_config")

        if self.module_id == ModuleId.BINARY_FEATURE_AE and not isinstance(
            self.module_config, ApiBinaryFeatureAeModuleConfig
        ):
            raise ValueError(
                "Binary Feature Mortality A/E configs require a binary feature module_config"
            )

        return self


class ApiListDatasetConfigsResults(BaseModel):
    """Response containing list of dataset configurations."""

    model_config = ConfigDict(extra="forbid")

    configs: list[ApiDatasetConfig]


def get_mortality_module_config(
    config: ApiDatasetConfig,
) -> ApiMortalityAeModuleConfig:
    if not isinstance(config.module_config, ApiMortalityAeModuleConfig):
        raise ValueError(
            f"Config '{config.id}' is for module '{config.module_id}', not mortality_ae"
        )
    return config.module_config


def get_binary_feature_module_config(
    config: ApiDatasetConfig,
) -> ApiBinaryFeatureAeModuleConfig:
    if not isinstance(config.module_config, ApiBinaryFeatureAeModuleConfig):
        raise ValueError(
            f"Config '{config.id}' is for module '{config.module_id}', not binary_feature_ae"
        )
    return config.module_config
