from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.binary_feature_ae.models.ai import ApiBinaryFeatureAiAction
from app.modules.binary_feature_ae.service import ai_skill_loader


def test_load_skill_valid_skill_loads() -> None:
    skill = ai_skill_loader.load_skill(
        ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE
    )

    assert skill.name == "explain_focused_rule"
    assert skill.action_type == ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE
    assert skill.response_schema == "rule_explanation"


def test_load_skill_unknown_action_fails() -> None:
    with pytest.raises(ValueError, match="Unknown AI action"):
        ai_skill_loader.load_skill("unknown_action")


def test_load_skill_missing_frontmatter_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    skill_path = tmp_path / "explain_focused_rule.md"
    skill_path.write_text("# missing frontmatter\n", encoding="utf-8")
    monkeypatch.setattr(ai_skill_loader, "SKILLS_DIR", tmp_path)
    monkeypatch.setattr(
        ai_skill_loader,
        "ACTION_SKILL_REGISTRY",
        {"explain_focused_rule": "explain_focused_rule.md"},
    )

    with pytest.raises(ValueError, match="frontmatter"):
        ai_skill_loader.load_skill("explain_focused_rule")


def test_load_skill_unapproved_model_profile_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    skill_path = tmp_path / "explain_focused_rule.md"
    skill_path.write_text(
        "---\n"
        "name: explain_focused_rule\n"
        "action_type: explain_focused_rule\n"
        "version: v1\n"
        "model_profile: not_approved\n"
        "temperature: 0.1\n"
        "response_schema: rule_explanation\n"
        "---\n"
        "{{ context_packet }}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_skill_loader, "SKILLS_DIR", tmp_path)
    monkeypatch.setattr(
        ai_skill_loader,
        "ACTION_SKILL_REGISTRY",
        {"explain_focused_rule": "explain_focused_rule.md"},
    )

    with pytest.raises(ValueError, match="Unapproved model profile"):
        ai_skill_loader.load_skill("explain_focused_rule")


def test_load_skill_unapproved_response_schema_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    skill_path = tmp_path / "explain_focused_rule.md"
    skill_path.write_text(
        "---\n"
        "name: explain_focused_rule\n"
        "action_type: explain_focused_rule\n"
        "version: v1\n"
        "model_profile: standard_interpretation\n"
        "temperature: 0.1\n"
        "response_schema: not_approved\n"
        "---\n"
        "{{ context_packet }}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_skill_loader, "SKILLS_DIR", tmp_path)
    monkeypatch.setattr(
        ai_skill_loader,
        "ACTION_SKILL_REGISTRY",
        {"explain_focused_rule": "explain_focused_rule.md"},
    )

    with pytest.raises(ValueError, match="Unapproved response schema"):
        ai_skill_loader.load_skill("explain_focused_rule")
