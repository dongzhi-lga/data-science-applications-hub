# Data Science Applications Hub

Data Science Applications Hub is a shared analytics platform for the data science
team. The repo is organized as one frontend shell, one backend, shared
configuration and storage infrastructure, and pluggable analysis modules.

Current active modules:

1. `mortality_ae` — Experience Study Mortality A/E
2. `binary_feature_ae` — Binary Feature Mortality A/E

The supported product workflow is now `config-first`:

1. Start in **Central Setup** at `/`
2. Choose a module
3. Upload a dataset
4. Load schema and complete module-specific mapping
5. Save a reusable dataset configuration
6. Reopen the saved config in the module analysis page

Legacy monitor flows and root-dataset discovery endpoints have been removed.

## Architecture

### Shared platform responsibilities

- shared frontend shell and routing
- shared backend core APIs
- reusable dataset config persistence
- shared local file storage under `.insight-hub/`
- schema profiling and generic upload handling

### Module responsibilities

- module-specific setup mapping
- module-specific analysis routes and service logic
- module-specific frontend pages, components, and API helpers

### Repository layout

- `app/core/`
  Shared backend models, routers, and services
- `app/modules/mortality_ae/`
  Mortality A/E models, calc, routes, and services
- `app/modules/binary_feature_ae/`
  Binary Feature models, routes, and services
- `client/src/core/`
  Shared frontend registry, HTTP layer, and shared APIs
- `client/src/modules/`
  Module-owned frontend pages, components, definitions, and APIs
- `docs/repo-structure.md`
  Detailed structure and ownership guide
- `docs/archive/`
  Historical presentations and experiment artifacts

## Storage

Saved configs and uploaded files live under:

```text
.insight-hub/
  dataset_configs.json
  files/
    <config_id>/
      <uploaded file>
```

Saved config records use the canonical shape:

- `module_id`
- `module_config`

## Active routes

### Frontend

- `/`
  Central Setup
- `/mortality-ae/analysis`
  Experience Study Mortality A/E
- `/binary-feature-ae/analysis`
  Binary Feature Mortality A/E

### Backend

- `GET /api/health`
- `POST /api/core/upload-schema`
- `GET /api/dataset-configs`
- `POST /api/dataset-configs`
- `GET /api/dataset-configs/{config_id}`
- `GET /api/dataset-configs/{config_id}/schema`
- `DELETE /api/dataset-configs/{config_id}`
- `POST /api/ae/upload-schema`
- `POST /api/ae/univariate-from-config`
- `POST /api/ae/univariate-from-csv`
- `POST /api/ae/insights/from-config`
- `POST /api/binary-feature-ae/calculate`
- `POST /api/binary-feature-ae/ai/explain-focused-rule`
  Preferred Binary Feature AI focused-rule explanation route
- `POST /api/binary-feature-ae/ai/explain-rule`
  Legacy alias for Binary Feature AI focused-rule explanations

## Supported file formats

- `.csv`
- `.xlsx`
- `.xls`
- `.parquet`

## Environment variables

- `INSIGHT_HUB_DATA_DIR`
  Overrides the data root used for `.insight-hub/`
- `INSIGHT_HUB_APPLICATION_ID_COLUMN`
  Overrides mortality application id detection
- `INSIGHT_HUB_MAX_UNIQUE_VALUES`
  Caps categorical values returned to the UI
- `INSIGHT_HUB_MAX_INSIGHT_DIMENSIONS`
  Caps candidate dimensions for mortality insights
- `INSIGHT_HUB_MAX_COLA_M1_CAUSES`
  Caps displayed mortality cause buckets
- `INSIGHT_HUB_MAX_SPLIT_GROUPS`
  Caps mortality split groups
- `INSIGHT_HUB_LLM_BASE_URL`
  OpenAI-compatible API root for Binary Feature AI actions
- `INSIGHT_HUB_LLM_API_KEY`
  Provider API key for Binary Feature AI actions
- `INSIGHT_HUB_LLM_MODEL`
  Provider model id for Binary Feature AI actions
- `INSIGHT_HUB_LLM_TIMEOUT_SECONDS`
  Optional timeout override for LLM calls
- `INSIGHT_HUB_LLM_MAX_RETRIES`
  Optional retry count for LLM calls

For local backend startup, `./scripts/local_start.sh` automatically loads `.env`
and then `.env.local` from the repo root if those files exist. Keep secrets in
`.env.local`; `.env.example` shows the expected shape.

For OpenAI specifically:

- `INSIGHT_HUB_LLM_BASE_URL` should be `https://api.openai.com/v1`
- working model ids for this Binary Feature explain flow include:
  `gpt-5.4-mini`, `gpt-5-mini`, `gpt-4.1-mini`, and `gpt-5.4`
- if you are optimizing for cost and latency, start with `gpt-5.4-mini`

## Local development

Requirements:

- Python `3.13`
- [`uv`](https://github.com/astral-sh/uv)
- Node.js `20+`

Backend:

```bash
uv sync
# Optional: cp .env.example .env.local and fill in your real LLM values
./scripts/local_start.sh
```

Frontend:

```bash
cd client
npm install
npm run dev
```

Default local URLs:

- frontend: [http://localhost:9200](http://localhost:9200)
- backend: [http://localhost:8000](http://localhost:8000)

## Adding a new module

1. Add backend logic under `app/modules/<module_id>/`
2. Add frontend logic under `client/src/modules/<module-slug>/`
3. Add a module definition file that plugs into `client/src/core/registry.ts`
4. Reuse shared dataset-config storage unless the module has a justified new
   persistence requirement
5. Keep shared concerns in `app/core/` and `client/src/core/`

See [docs/repo-structure.md](/Users/amberwang/Desktop/dzw/data-science-applications-hub/docs/repo-structure.md) for the detailed ownership model.
