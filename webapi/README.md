# webapi — HOOPS AI WebAPI (minimal sample)

FastAPI application that exposes the following endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/files/upload` | Upload a CAD file; returns `file_id` (SHA-256 dedup) |
| `GET`  | `/files/` | List uploaded files |
| `POST` | `/CAD/viewer` | Open a CAD file in the HOOPS Web Viewer |
| `DELETE` | `/CAD/viewer` | Close viewer(s) for the current session |
| `GET` | `/CAD/viewer/show` | Serve the Web Viewer HTML page (accessed via `viewer_url`) |
| `GET` | `/CAD/viewer/colors` | Return face color data for MFR visualization |
| `POST` | `/MFR/inference` | Run Manufacturing Feature Recognition |
| `POST` | `/BRep/attributes` | Extract per-face and per-edge B-rep attributes |

## Prerequisites

- Python 3.12
- HOOPS AI SDK installed in the same Python environment
  (obtain from your Tech Soft 3D distribution; not available on PyPI)
- A valid HOOPS AI license key
- A valid HOOPS Visualize Web license key (required for the CAD viewer endpoints)

## Setup

### 1. Install dependencies

Install the WebAPI dependencies into the **HOOPS AI virtual environment**:

**Windows:**
```bat
<HOOPS_AI_INSTALL_DIR>\.venv\Scripts\pip.exe install -r requirements.txt
```

**Linux:**
```bash
<HOOPS_AI_INSTALL_DIR>/.venv/bin/pip install -r requirements.txt
```

> On Ubuntu 22.04+ the system Python is externally managed (PEP 668) and will reject bare `pip install`.
> Using the HOOPS AI venv's pip avoids this restriction.

### 2. Create `.env`

**Windows:**
```bat
copy .env.example .env
```

**Linux:**
```bash
cp .env.example .env
```

Edit `.env` — set `HOOPS_AI_LICENSE`, `HOOPS_AI_SDK_DIR`, `HOOPS_AI_MFR_MODEL_NAME`, etc.

### 3. Copy the HOOPS Web Viewer JS asset into `static/`

**Windows:**
```bat
copy "<HOOPS_AI_INSTALL_DIR>\.venv\Lib\site-packages\hoops_viewer\static\javascript\communicator\web-viewer-monolith\hoops-web-viewer-monolith.mjs" "static\"
```

**Linux:**
```bash
cp "<HOOPS_AI_INSTALL_DIR>/.venv/lib/python3.12/site-packages/hoops_viewer/static/javascript/communicator/web-viewer-monolith/hoops-web-viewer-monolith.mjs" "static/"
```

## Start the server

Run from the `webapi/` directory using the Python executable from your HOOPS AI virtual environment.

**Windows:**
```bat
<HOOPS_AI_INSTALL_DIR>\.venv\Scripts\python.exe main.py --host 0.0.0.0 --port 8000
```

**Linux:**
```bash
<HOOPS_AI_INSTALL_DIR>/.venv/bin/python main.py --host 0.0.0.0 --port 8000
```

> **Note (Linux):** If the server is not reachable from other machines, check the firewall. On Ubuntu with `ufw` enabled, open the port with:
> ```bash
> sudo ufw allow 8000/tcp
> ```
>
> For running HOOPS AI on a headless Ubuntu server (no GPU, no monitor), refer to the [community forum post](https://forum.techsoft3d.com/t/i-tried-running-hoops-ai-v1-1-headless-on-ubuntu-24-04-ec2/5165) for step-by-step instructions.

Interactive API docs are available at <http://127.0.0.1:8000/docs>.

## Environment variables (`.env`)

| Variable | Description |
|----------|-------------|
| `HOOPS_AI_LICENSE` | Your HOOPS AI & Visualize Web license key |
| `HOOPS_AI_SDK_DIR` | Absolute path to the HOOPS AI SDK root directory (e.g. `C:/SDK/HOOPS_AI/V1.1`) |
| `HOOPS_AI_MFR_MODEL_NAME` | Filename of the trained MFR model checkpoint |

## Notes

- The `uploads/` and `out/` directories are created automatically on first run.
- `static/*.mjs` is excluded from version control — copy it manually (see Setup above).
- This is a **minimal sample** — it is not production-ready.
