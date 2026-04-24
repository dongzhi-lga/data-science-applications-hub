# Current Binary Feature AI Status

The Binary Feature Mortality A/E module currently has one working AI pattern:
Explain Focused Rule.

## Trust boundary

- Uploaded data and saved config mappings own the mortality metrics.
- Python deterministic services own filtering, projection, scoring,
  fingerprints, packet construction, validation, and fallback responses.
- Skill Markdown owns AI behavior instructions for the enabled action.
- The LLM interprets the packet only; it does not calculate or override
  actuarial metrics.
- Deterministic fallback protects the user experience when the LLM is
  unconfigured, unavailable, or returns invalid output.

## Enabled action

- Preferred action name: `explain_focused_rule`
- Preferred route: `POST /api/binary-feature-ae/ai/explain-focused-rule`
- Legacy route kept for compatibility:
  `POST /api/binary-feature-ae/ai/explain-rule`
- Skill file:
  `app/modules/binary_feature_ae/skills/explain_focused_rule.md`

Both AI routes call the same backend orchestrator and return the same response
shape. The frontend should use the preferred focused-rule helper, while the
legacy helper remains available as an alias.

## Current flow

1. Build the deterministic visible-view packet from the same state used by the
   table.
2. Build a deterministic fallback response from the packet.
3. Check whether LLM configuration is present.
4. Load and render the focused-rule skill.
5. Request structured LLM output.
6. Validate action type, fingerprint, focused row identity, rule label,
   evidence refs, and unsafe language.
7. Return the validated LLM response or the deterministic fallback.

## Deferred actions

The shared AI model types include future action names for:

- `summarize_view`
- `compare_rules`
- `analyze_divergence`

Those actions are not enabled yet. The only registered skill today is
`explain_focused_rule`, and unknown or unregistered actions should fail safely.

## Compatibility notes

- Keep `ai_explain.py` as a compatibility wrapper for now.
- Keep the legacy `/api/binary-feature-ae/ai/explain-rule` endpoint for now.
- Do not change `state_fingerprint`, response schema, evidence refs, or fallback
  output during stabilization cleanup.
