from __future__ import annotations

import re
from pathlib import Path

import yaml

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    BinaryFeatureAiSkillDefinition,
)

ACTION_SKILL_REGISTRY = {
    "explain_focused_rule": "explain_focused_rule.md",
}

APPROVED_RESPONSE_SCHEMAS = {
    "rule_explanation",
}

APPROVED_MODEL_PROFILES = {
    "standard_interpretation",
}

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"


def _split_frontmatter(raw: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.DOTALL)
    if match is None:
        raise ValueError("Skill file is missing valid YAML frontmatter")
    return match.group(1), match.group(2)


def load_skill(
    action: ApiBinaryFeatureAiAction | str,
) -> BinaryFeatureAiSkillDefinition:
    action_name = getattr(action, "value", action)
    if action_name not in ACTION_SKILL_REGISTRY:
        raise ValueError(f"Unknown AI action: {action_name}")

    skill_path = (SKILLS_DIR / ACTION_SKILL_REGISTRY[action_name]).resolve()
    if skill_path.parent != SKILLS_DIR.resolve():
        raise ValueError(
            "Skill file path resolved outside the approved skills directory"
        )

    raw = skill_path.read_text(encoding="utf-8")
    frontmatter_text, body = _split_frontmatter(raw)
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        raise ValueError(
            "Skill frontmatter could not be parsed as YAML"
        ) from exc

    if not isinstance(frontmatter, dict):
        raise ValueError("Skill frontmatter must decode to an object")

    required_fields = {
        "name",
        "action_type",
        "version",
        "model_profile",
        "temperature",
        "response_schema",
    }
    missing_fields = sorted(required_fields - set(frontmatter))
    if missing_fields:
        missing_fields_label = ", ".join(missing_fields)
        raise ValueError(
            "Skill frontmatter is missing required fields: "
            f"{missing_fields_label}"
        )

    skill = BinaryFeatureAiSkillDefinition.model_validate(
        {
            **frontmatter,
            "body": body,
        }
    )

    if skill.name != action_name:
        raise ValueError("Skill name does not match the requested action")
    if skill.action_type != ApiBinaryFeatureAiAction(action_name):
        raise ValueError(
            "Skill action_type does not match the requested action"
        )
    if skill.model_profile not in APPROVED_MODEL_PROFILES:
        raise ValueError(f"Unapproved model profile: {skill.model_profile}")
    if skill.response_schema not in APPROVED_RESPONSE_SCHEMAS:
        raise ValueError(f"Unapproved response schema: {skill.response_schema}")

    return skill
