# Data Science Applications Hub

**Data Science Applications Hub** is a local-only multi-function analysis tool with:
- A FastAPI backend for schema inference, saved-config workflows, A/E computation, and diagnostics
- A Quasar (Vue 3 + TypeScript) frontend for a central setup experience and module-specific analysis pages
- DuckDB-powered diagnostic insights for fast ranked segment discovery

## Project Overview

Data Science Applications Hub supports local analysis of mortality datasets in CSV, Excel, and Parquet format. Phase 1 includes the **Experience Study Mortality A/E** module with:
- Univariate A/E analysis with numeric, date, and categorical variables
- Optional split overlays, exclusions, polynomial fit, treemap, and tabular views
- Cause-of-death breakdowns
- Saved dataset configurations with reusable column mappings
- Diagnostic insights that automatically rank high-variance 1D and 2D segments and let you drill back into the existing A/E workflow

The main user flow is now hub-backed:
1. Open the **Central Setup** page.
2. Select the **Experience Study Mortality A/E** module.
3. Upload a dataset and save a dataset configuration with its column mapping.
4. Open the saved configuration in the module analysis page.
5. Run univariate A/E directly from the stored backend file.
6. Review the `Diagnostic insights` panel.
7. Click `Drill` on an insight to apply the suggested `x` and optional `split`, then rerun analysis.

**Architecture**
- **Backend:** Python 3.13, FastAPI, Pandas, DuckDB, Pydantic, Uvicorn
- **Frontend:** Vue 3, Quasar, TypeScript, Plotly.js

---

## Backend

### Requirements

- Python 3.13
- [`uv`](https://github.com/astral-sh/uv)

### Installation & Run

```bash
uv sync
./scripts/local_start.sh
```

Verify the backend at [http://localhost:8000/api/health](http://localhost:8000/api/health).

### Supported Datasets & File Formats

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Parquet (`.parquet`)
- File type is auto-detected by extension.
- By default, datasets can live in the project root. Set `INSIGHT_HUB_DATA_DIR` to override that directory.
- Saved dataset configs and their uploaded files are stored under `.insight-hub/` and persist across backend restarts.

### Data Expectations

- **Time-series monitoring** expects a date column and a numeric value column.
- **A/E analysis** uses saved or uploaded column mappings for fields such as policy number, `MAC`, `MEC`, `MAN`, `MEN`, optional `MOC`, COLA fields, and face amount where applicable.

---

## API Endpoints

### Dataset Management

- `GET /api/datasets` — List available datasets from the configured data directory
- `GET /api/datasets/{dataset_name}/schema` — Infer dataset schema
- `GET /api/datasets/{dataset_name}/cola` — Run cause-of-death analysis

### Saved Dataset Configurations

- `GET /api/dataset-configs` — List saved dataset configurations
- `POST /api/dataset-configs` — Create a saved dataset configuration with uploaded file and column mapping
- `GET /api/dataset-configs/{config_id}` — Fetch a saved dataset configuration
- `GET /api/dataset-configs/{config_id}/schema` — Infer schema from the stored file behind a saved config
- `GET /api/dataset-configs/{config_id}/file` — Download the stored file for a saved config
- `DELETE /api/dataset-configs/{config_id}` — Delete a saved config and its stored file

### Core Schema Profiling

- `POST /api/core/upload-schema` — Infer generic schema metadata for the central setup page

### Monitor Endpoints (Legacy/Internal)

- `POST /api/monitor/from-dataset` — Run time-series monitoring from a named dataset
- `POST /api/monitor/from-csv` — Run time-series monitoring from an uploaded file

Example:

```bash
curl -sS -X POST http://localhost:8000/api/monitor/from-dataset \
  -H 'content-type: application/json' \
  -d '{"dataset_name":"dataset.csv","date_column":"date","value_column":"deaths"}'
```

### A/E Analysis Endpoints

- `POST /api/ae/univariate` — Run univariate A/E from a named dataset
- `POST /api/ae/univariate-from-config` — Run univariate A/E from a saved dataset configuration
- `POST /api/ae/univariate-from-csv` — Run univariate A/E from an uploaded file
- `POST /api/ae/upload-schema` — Infer schema from an uploaded file
- `POST /api/ae/variable-labels` — Get available variable labels
- `POST /api/ae/insights/from-config` — Run DuckDB-backed diagnostic insight discovery from a saved dataset configuration

Example univariate payload:

```json
{
  "dataset_name": "dataset.csv",
  "x_variable": {
    "kind": "numeric",
    "name": "age",
    "binning": "quintile",
    "bin_count": 5
  },
  "split_variable": null,
  "column_mapping": {
    "policy_number_column": "policy_id",
    "mac_column": "mac",
    "mec_column": "mec",
    "man_column": "man",
    "men_column": "men"
  }
}
```

Example diagnostic insight request:

```json
{
  "config_id": "your-config-id",
  "max_results_per_metric": 25
}
```

Diagnostic insight responses include:
- `count_insights`
- `amount_insights`
- Per-insight metrics for sample size, actual, expected, variance, and A/E
- A drill payload that maps directly into the univariate A/E controls

---

## Frontend

### Requirements

- Node.js 20+

### Installation & Run

```bash
cd client
npm install
npm run dev
```

Open [http://localhost:9200](http://localhost:9200).

Phase 1 routes:
- `/` — Central Setup
- `/mortality-ae/analysis` — Experience Study Mortality A/E analysis page
- `/monitor` — Legacy compatibility redirect to the mortality analysis page

### Features

- **Data Upload & Configuration**
  - Use the central setup page to upload CSV, Excel, or Parquet files
  - Infer a generic schema first, then apply module-specific setup
  - Save reusable dataset configurations with mortality column mappings
- **Univariate A/E Analysis**
  - Numeric, date, and categorical `x` variables
  - Uniform, quintile, or custom numeric binning
  - Optional split overlays
  - Categorical grouping and exclusions
  - Polynomial fit options
- **Visualizations**
  - Interactive A/E scatter plot
  - Treemap for count and amount distribution
  - Tabular A/E results
  - COLA stacked bars
- **Diagnostic Insights**
  - Auto-load for saved dataset configurations
  - DuckDB-ranked 1D and 2D segments
  - Separate `Count` and `Amount` tabs
  - Collapsible and expandable `Diagnostic insights` panel
  - One-click drill into the existing univariate A/E workflow

---

## Development & Testing

- **Backend**
  - Install dependencies: `uv sync`
  - Run tests: `UV_CACHE_DIR=.uv-cache PYTHONPATH=. uv run pytest`
- **Frontend**
  - Install dependencies: `cd client && npm install`
  - Run dev server: `cd client && npm run dev`
  - Run typecheck: `cd client && npm run typecheck`
  - Linting and formatting are configured in `client/package.json`

### Developer Note

Phase 2 makes `.insight-hub/` and `INSIGHT_HUB_*` the canonical storage names.
Legacy `.aemonitor/` storage and `AEMONITOR_*` environment variables are still
accepted temporarily for backward compatibility during the migration window.

---

## File Format Support

All major workflows support CSV, Excel, and Parquet files. See `FILE_FORMAT_SUPPORT.md` for details.

---

## License

MIT License. See `LICENSE` file.
