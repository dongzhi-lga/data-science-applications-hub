from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ApiBinaryFeatureKnowledgeStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_pack_id: str | None = None
    knowledge_pack_status: str = "none"
    source_names: list[str] = Field(default_factory=list)
