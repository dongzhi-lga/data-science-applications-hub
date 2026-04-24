# Repo Structure Overview

This repository is maintained as a shared analytics platform with pluggable
modules. The guiding rule is:

- shared platform concerns belong in `app/core/` and `client/src/core/`
- analysis-specific concerns belong inside a module folder

## Top-level folders

- `app/`
  Backend application code
- `client/`
  Frontend application code
- `docs/`
  Architecture docs and archived historical materials
- `scripts/`
  Local developer scripts
- `tests/`
  Backend unit and integration tests

## Backend ownership

### `app/core/`

Shared backend platform layer.

- `models/dataset_config.py`
  Canonical saved-config contracts shared by all modules
- `models/schema.py`
  Generic schema-profiling response types
- `routers/data_io.py`
  Generic upload-to-schema profiling endpoint
- `routers/dataset_configs.py`
  Shared dataset-config CRUD routes
- `routers/health.py`
  Health endpoint
- `service/dataframe_loader.py`
  Shared dataframe loading for supported file formats
- `service/dataset_config.py`
  Saved-config persistence and file lookup
- `service/schema_profile.py`
  Generic schema inference
- `service/storage.py`
  `.insight-hub` storage bootstrap and path normalization

### `app/modules/mortality_ae/`

Mortality A/E module ownership.

- `models/ae.py`
  Mortality request/response contracts
- `models/chart.py`
  Mortality chart table models
- `models/insights.py`
  Mortality insights contracts
- `models/schema.py`
  Mortality-specific schema and mapping suggestions
- `calc/ae_univariate.py`
  Univariate mortality calculations
- `service/ae_univariate.py`
  Mortality analysis orchestration
- `service/ae_insights.py`
  Mortality diagnostic insight ranking
- `service/dataset_schema.py`
  Mortality schema inference from uploads and saved configs
- `routers/ae.py`
  Mortality endpoints

### `app/modules/binary_feature_ae/`

Binary Feature module ownership.

- `models/triage.py`
  Binary Feature request/response contracts
- `models/ai.py`
  Binary Feature AI action, packet, evidence, and response contracts
- `service/binary_calc.py`
  Binary Feature filtering, scoring, and response shaping
- `service/view_state.py`
  Deterministic visible-view state used by calculation and AI packets
- `service/ai_orchestrator.py`
  Binary Feature AI orchestration with validation and deterministic fallback
- `service/ai_packets.py`
  AI context packet builders sourced from deterministic view state
- `service/ai_skill_loader.py`
  Module skill registry and skill frontmatter validation
- `service/ai_skill_renderer.py`
  Skill prompt rendering with immutable context packets
- `service/ai_validation.py`
  Binary Feature-specific structured AI response validation
- `service/ai_fallbacks.py`
  Deterministic fallback responses for AI actions
- `service/ai_baselines.py`
  Rule baseline metrics used by AI packets and fallback explanations
- `service/ai_explain.py`
  Legacy compatibility wrapper for the focused-rule explain flow
- `routers/binary_feature.py`
  Binary Feature calculate and AI API routes
- `skills/explain_focused_rule.md`
  Skill instructions for the currently enabled AI action

## Frontend ownership

### `client/src/core/`

Shared frontend platform layer.

- `api/dataset-configs.ts`
  Shared dataset-config CRUD client
- `api/data-io.ts`
  Generic upload-to-schema client
- `http.ts`
  Shared fetch helpers
- `registry.ts`
  Shared module registry types and active module aggregation
- `types/schema.ts`
  Generic schema response types

### `client/src/modules/mortality-ae/`

Mortality module ownership.

- `definition.ts`
  Mortality setup state, validation, and config creation contract
- `api.ts`
  Mortality-specific backend calls
- `pages/`
  Mortality analysis page
- `components/`
  Mortality setup and visualization components
- `composables/`
  Mortality page state and variable builder logic
- `types.ts`
  Mortality analysis request/response types

### `client/src/modules/binary-feature-ae/`

Binary Feature module ownership.

- `definition.ts`
  Binary Feature setup state, validation, and config creation contract
- `api.ts`
  Binary Feature analysis and AI request client
- `pages/`
  Binary Feature analysis page
- `components/`
  Binary Feature visual and triage UI
- `components/BinaryFeatureAiPanel.vue`
  Focused-rule AI explanation panel
- `components/BinaryFeatureAiStateBanner.vue`
  AI source, fallback, stale-state, and validation banner
- `components/BinaryFeatureEvidenceChips.vue`
  Clickable AI evidence references back to visible table rows
- `constants.ts`
  Binary Feature display and mapping constants

### Shared pages and layout

- `client/src/pages/HubCentralSetup.vue`
  Hub-first setup and saved-config library page
- `client/src/layouts/MainLayout.vue`
  Shared app layout and module navigation

## Current platform boundary

### Shared platform code

- generic schema upload/profile
- dataset-config CRUD
- storage bootstrap and file persistence
- frontend shell and module registry

### Module-specific code

- mapping requirements for a module
- calculation and insight logic
- module-specific routes and analysis pages
- module-specific response shapes and UI components

## Removed legacy surfaces

The following were intentionally removed during cleanup:

- `/api/monitor/*` backend monitor routes
- frontend `/monitor` redirect
- root-dataset discovery endpoints under `/api/datasets`
- legacy monitor models, calc, services, and tests
- runtime `.aemonitor` storage migration
- `AEMONITOR_*` environment aliases
- runtime saved-config fallbacks for missing `module_id`,
  missing `performance_type`, and legacy `column_mapping` payloads
- thin router re-export wrappers in `app/routers/`
- stale frontend monitor helpers and unused chart helper components

Historical materials were archived to:

- `docs/archive/presentations/`
- `docs/archive/experiments/`

## Where to add new modules

Backend:

1. Create `app/modules/<module_id>/`
2. Add models, service logic, and routers inside that folder
3. Reuse `app/core/` for shared storage/config concerns

Frontend:

1. Create `client/src/modules/<module-slug>/`
2. Add `definition.ts` for setup state and config creation
3. Add module pages, components, and APIs inside that folder
4. Register the module in `client/src/core/registry.ts`

## Remaining technical debt

- Mortality still supports a direct-upload analysis path in addition to the
  shared config-first path. It is active, but it is a second workflow surface to
  maintain.
- Frontend route-level code splitting is still a follow-up improvement. The app
  works correctly, but bundle growth should be watched as modules are added.
- Saved-config storage is filesystem-backed and local. If the hub grows into a
  multi-user or deployed product, storage and auth boundaries will need a new
  design.
