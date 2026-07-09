# webapi — HOOPS AI WebAPI (minimal sample)

FastAPI application that exposes three endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/files/upload` | Upload a CAD file; returns `file_id` (SHA-256 dedup) |
| `GET`  | `/files/` | List uploaded files |
| `POST` | `/CAD/viewer` | Open a CAD file in the HOOPS Web Viewer |
| `DELETE` | `/CAD/viewer` | Close viewer(s) for the current session |
| `POST` | `/MFR/inference` | Run Manufacturing Feature Recognition |

## Prerequisites

- Python 3.12+
- HOOPS AI SDK installed in the same Python environment
  (obtain from your Tech Soft 3D distribution; not available on PyPI)
- A valid HOOPS AI license key

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env (copy from example and fill in your values)
cp .env.example .env
# Edit .env — set HOOPS_AI_LICENSE, HOOPS_AI_NOTEBOOK_DIR, HOOPS_AI_MFR_MODEL_NAME, etc.

# 3. Copy HOOPS Web Viewer JS asset into static/
#    (hoops-web-viewer-monolith.mjs — part of the HOOPS AI distribution)
mkdir -p static
cp /path/to/hoops-web-viewer-monolith.mjs static/
```

## Start the server

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Interactive API docs are available at <http://127.0.0.1:8000/docs>.

## Environment variables (`.env`)

| Variable | Description |
|----------|-------------|
| `HOOPS_AI_LICENSE` | Your HOOPS AI license key |
| `HOOPS_AI_NOTEBOOK_DIR` | Absolute path to the HOOPS AI notebooks output directory |
| `HOOPS_AI_MFR_MODEL_NAME` | Filename of the trained MFR model checkpoint |
| `HOOPS_AI_MFR_FLOW_NAME` | Name of the MFR ETL flow (for labels_description.json) |

## Notes

- The `uploads/` and `out/` directories are created automatically on first run.
- Place `hoops-web-viewer-monolith.mjs` in `static/` for the web viewer to work.
- This is a **minimal sample** — it is not production-ready.
