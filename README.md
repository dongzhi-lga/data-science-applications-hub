# Data Science Applications Hub

Data Science Applications Hub is the data science team's shared application hub.
Instead of maintaining separate single-purpose tools, this repository hosts
multiple analysis workflows behind one frontend, one backend, and one shared
configuration/storage model.

The project is intentionally hub-first:

- users start from a single **Central Setup** page
- datasets are uploaded once and saved as reusable configurations
- each saved configuration opens the correct analysis page
- new applications can plug into the same pattern as the hub grows

Today the hub has **2 active applications**:

1. **Experience Study Mortality A/E**
2. **Binary Feature Mortality A/E**

The codebase is already structured for more modules to be added through the
shared registry, routing, and dataset-config workflow.

## What The Hub Does

### Central Setup

Route: `/`

This is the landing page for the whole system. It lets users:

- choose an active analysis module
- upload a CSV, Excel, or Parquet file
- infer a generic schema
- complete module-specific field mapping
- save a reusable dataset configuration
- reopen saved configurations directly into the correct analysis page

All saved configs are backed by local file storage under `.insight-hub/`.

### Experience Study Mortality A/E

Route: `/mortality-ae/analysis`

This is the main exploratory mortality analysis workflow in the hub. It is
config-backed: users select a saved mortality dataset configuration and then run
analysis against the stored file and mappings.

Current capabilities include:

- numeric, date, categorical, and composite `A x B` x-axis variables
- optional split variable with the same variable types
- uniform, quintile, and custom binning
- custom categorical grouping and explicit group positioning
- count-based and amount-based A/E outputs
- 95% confidence intervals
- optional polynomial best-fit overlays
- scatter plots, treemaps, and tabular outputs
- cause-of-death claim summaries and stacked bar visuals
- DuckDB-ranked diagnostic insights across 1D and 2D segments
- one-click drill from an insight back into the mortality controls

### Binary Feature Mortality A/E

Route: `/binary-feature-ae/analysis`

This module is built for triaging pre-aggregated rule or binary-feature output.
It expects a saved configuration with a mapped ruleset-style dataset, then
provides an interactive review surface for candidate rules.

Current capabilities include:

- config-driven mapping for rule, hit, claim, A/E, CI, and COLA columns
- category, significance, search, minimum hit count, and minimum claim count filters
- 95%, 90%, and 80% confidence interval views
- KPI summary cards
- scatter plot for rule triage
- focused detail cards for the selected rule
- compare charts for selected rules
- tabular compare/triage grid
- pinning workflow for follow-up candidates

### Legacy / Compatibility Surface

The repo still contains older monitoring support:

- frontend route `/monitor` redirects to the mortality A/E page
- backend endpoints under `/api/monitor/*` still exist for legacy mortality
  time-series monitoring workflows

## Typical User Flow

1. Open **Central Setup**.
2. Select the module you want to use.
3. Upload a dataset file.
4. Load schema and complete the module-specific mapping.
5. Save the configuration.
6. Open the saved configuration from the hub table.
7. Run the module workflow against the saved file.

For the mortality module, diagnostic insights are automatically loaded from the
saved configuration and can be drilled back into the main analysis controls.

## Architecture

### Stack

- Backend: FastAPI, Pydantic, Pandas, DuckDB, NumPy, SciPy, Uvicorn
- Frontend: Vue 3, Quasar, TypeScript, Vite, Plotly
- Storage: local filesystem-backed config and dataset storage

### Repository Layout

- `app/`
  FastAPI app, routers, services, models, and calculation logic
- `app/modules/mortality_ae/`
  Mortality A/E API routing
- `app/modules/binary_feature_ae/`
  Binary Feature Mortality A/E API routing and service logic
- `client/`
  Vue/Quasar frontend, hub pages, module pages, and shared registry
- `client/src/core/registry.ts`
  Active module registration for the frontend hub
- `scripts/local_start.sh`
  backend dev startup script
- `tests/`
  backend unit and integration tests

### Shared Hub Design

The hub works because both active applications share the same core patterns:

- a common landing/setup page
- module registration in the frontend registry
- reusable saved dataset configurations
- shared local file storage
- module-specific backend routes layered on top of shared storage/services

That is the main reason this repo can grow into a broader applications hub
instead of staying a single analysis tool.

## Data And Storage

### Supported File Formats

The hub supports:

- `.csv`
- `.xlsx`
- `.xls`
- `.parquet`

Format is detected automatically from the filename extension.

### Data Sources

The backend supports two main dataset patterns:

- **root dataset directory**
  files discovered through `/api/datasets`
- **saved hub configurations**
  uploaded files copied into hub-managed storage and reopened through
  `/api/dataset-configs`

The current frontend flow is centered on saved configurations.

### Storage Layout

By default, hub-managed storage is created in:

```text
.insight-hub/
  dataset_configs.json
  files/
    <config_id>/
      <uploaded file>
```

Saved files persist across backend restarts.

### Legacy Migration

Older `.aemonitor/` storage is still recognized and migrated to
`.insight-hub/` on startup. Legacy `AEMONITOR_*` environment variables are also
still accepted during the migration window.

## Environment Variables

The most useful runtime settings are:

- `INSIGHT_HUB_DATA_DIR`
  override the root directory used for dataset discovery and hub storage
- `INSIGHT_HUB_APPLICATION_ID_COLUMN`
  force the application/policy id column for mortality workflows
- `INSIGHT_HUB_MAX_UNIQUE_VALUES`
  cap categorical values returned to the UI
- `INSIGHT_HUB_MAX_INSIGHT_DIMENSIONS`
  cap the number of candidate dimensions considered by diagnostic insights
- `INSIGHT_HUB_MAX_COLA_M1_CAUSES`
  cap displayed cause-of-death buckets
- `INSIGHT_HUB_MAX_SPLIT_GROUPS`
  cap the number of split groups allowed in mortality analysis

Legacy aliases with the `AEMONITOR_` prefix still work.

## Local Development

### Requirements

- Python `3.13`
- [`uv`](https://github.com/astral-sh/uv)
- Node.js `20+`

### Backend

Install dependencies:

```bash
uv sync
```

Start the API server:

```bash
./scripts/local_start.sh
```

Backend health check:

- [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Frontend

Install dependencies:

```bash
cd client
npm install
```

Start the frontend:

```bash
cd client
npm run dev
```

Open:

- [http://localhost:9200](http://localhost:9200)

The frontend is configured to call the backend at `http://localhost:8000`.

## API Overview

### Shared Endpoints

- `GET /api/health`
- `POST /api/core/upload-schema`
- `GET /api/datasets`
- `GET /api/datasets/{dataset_name}/schema`
- `GET /api/datasets/{dataset_name}/cola`
- `GET /api/dataset-configs`
- `POST /api/dataset-configs`
- `GET /api/dataset-configs/{config_id}`
- `GET /api/dataset-configs/{config_id}/schema`
- `GET /api/dataset-configs/{config_id}/file`
- `DELETE /api/dataset-configs/{config_id}`

### Mortality A/E Endpoints

- `POST /api/ae/univariate`
- `POST /api/ae/univariate-from-config`
- `POST /api/ae/univariate-from-csv`
- `POST /api/ae/upload-schema`
- `POST /api/ae/variable-labels`
- `POST /api/ae/insights/from-config`

### Binary Feature Endpoints

- `POST /api/binary-feature-ae/calculate`

### Legacy Monitor Endpoints

- `POST /api/monitor/from-dataset`
- `POST /api/monitor/from-csv`

## Module-Specific Data Expectations

### Mortality A/E

The mortality workflow expects actual and expected metrics, typically including:

- `MAC`
- `MEC`
- `MAN`
- `MEN`

Optional mappings include:

- policy/application id
- face amount
- `MOC`
- `COLA_M1`

### Binary Feature Mortality A/E

The binary feature workflow expects a pre-aggregated ruleset-style table with:

- rule identifiers and labels
- first-date and category fields
- hit and claim metrics
- A/E ratio
- 95%, 90%, and 80% confidence interval columns
- COLA percentage columns

## Testing

Backend tests:

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=. uv run pytest
```

Frontend type-check:

```bash
cd client
npm run typecheck
```

Optional frontend production build:

```bash
cd client
npm run build
```

## Notes For Future Modules

If you add another application to the hub, the current codebase already gives
you the main extension points:

- add a new module definition in `client/src/core/registry.ts`
- add a new module analysis page and setup component in `client/src/modules/`
- add backend routes and services under `app/modules/`
- reuse the shared dataset-config and storage flow whenever possible

That is the core purpose of this repository: a single applications hub for the
data science team, with multiple focused web applications living behind a shared
platform.
