from __future__ import annotations

import json
from dataclasses import dataclass

from app.modules.binary_feature_ae.models.ai import (
    BinaryFeatureAiExplainFocusedRulePacket,
    BinaryFeatureAiSkillDefinition,
)

_CONTEXT_PACKET_PLACEHOLDER = "{{ context_packet }}"


@dataclass(frozen=True)
class RenderedSkillPrompt:
    system_prompt: str
    user_prompt: str


def render_skill_prompt(
    *,
    skill: BinaryFeatureAiSkillDefinition,
    packet: BinaryFeatureAiExplainFocusedRulePacket,
) -> RenderedSkillPrompt:
    if _CONTEXT_PACKET_PLACEHOLDER not in skill.body:
        raise ValueError(
            "Skill template is missing the context_packet placeholder"
        )

    context_packet = json.dumps(
        packet.model_dump(mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    )
    system_prompt = skill.body.replace(
        _CONTEXT_PACKET_PLACEHOLDER, context_packet
    )
    if "{{" in system_prompt or "}}" in system_prompt:
        raise ValueError("Skill template contains unsupported placeholders")

    return RenderedSkillPrompt(
        system_prompt=system_prompt,
        user_prompt=(
            "Analyze the provided context packet and return strict JSON only."
        ),
    )
