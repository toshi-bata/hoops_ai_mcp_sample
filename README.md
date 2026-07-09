# hoops_ai_mcp_sample

**A minimal sample that exposes HOOPS AI as a FastAPI WebAPI and calls it from Claude Desktop via MCP.**
Created as a simple, self-contained example for a forum article.

> ⚠️ This is a minimal sample for article purposes — it is not production-ready.
> Error handling and security are intentionally kept minimal.

---

## Overview

```
Claude Desktop
    │  MCP (stdio)
    ▼
mcp_server/server.py   — FastMCP, 3 MCP tools
    │  HTTP (httpx)
    ▼
webapi/main.py         — FastAPI, 3 endpoint groups
    │  Python API
    ▼
HOOPS AI SDK           — CAD loading / SCS export / MFR inference
```

Only three feature groups are implemented:

| Feature | WebAPI endpoint | MCP tool |
|---------|-----------------|----------|
| File upload | `POST /files/upload` | `upload_cad_model` |
| CAD viewer | `POST /CAD/viewer` | `open_cad_viewer` |
| MFR inference | `POST /MFR/inference` | `run_mfr_inference` |

---

## Prerequisites

- **Python 3.12**
- **HOOPS AI SDK V1.1** installed in the same Python environment
  (obtain from your Tech Soft 3D distribution)
- **A valid HOOPS AI and Visualize Web license key**
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- **Claude Desktop** (required for MCP usage)

> No sample CAD files are included. Try it with your own STEP or IGES files.

---

## Getting started

### Step 1 — Start the WebAPI server

```bash
cd webapi

# Install dependencies
pip install -r requirements.txt

# Create .env from the example and fill in your values
cp .env.example .env
# HOOPS_AI_LICENSE=<your license key>
# HOOPS_AI_NOTEBOOK_DIR=C:/path/to/hoops_ai/notebooks
# HOOPS_AI_MFR_MODEL_NAME=<model filename>.ckpt
# HOOPS_AI_MFR_FLOW_NAME=<flow name>

# Copy the HOOPS Web Viewer JS asset (from the HOOPS AI distribution)
mkdir -p static
cp /path/to/hoops-web-viewer-monolith.mjs static/

# Start the server
uvicorn main:app --host 127.0.0.1 --port 8000
```

Interactive API docs: <http://127.0.0.1:8000/docs>

### Step 2 — Register the MCP server with Claude Desktop

Add the following entry to `claude_desktop_config.json`
(Windows: `%APPDATA%\Claude\claude_desktop_config.json`,
macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hoops-ai-sample": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/git/toshi-bata/HOOPS_AI/hoops_ai_mcp_sample/mcp_server",
        "run",
        "server.py"
      ],
      "env": {
        "HOOPS_WEBAPI_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

Restart Claude Desktop after editing the file.
See [`mcp_server/README.md`](mcp_server/README.md) for more details.

### Step 3 — Try it in Claude Desktop

With the WebAPI running, pass a local CAD file path in the chat:

```
Run MFR inference on C:/parts/bracket.step
```

```
Open C:/parts/housing.stp in the CAD viewer
```

Claude will automatically call `upload_cad_model` → `run_mfr_inference`
(or `open_cad_viewer`) in sequence.

---

## Repository layout

```
hoops_ai_mcp_sample/
├── webapi/
│   ├── main.py              # FastAPI app — license init via lifespan
│   ├── core.py              # file_id management, CAD viewer, MFR inference
│   ├── routers/
│   │   ├── files.py         # POST /files/upload, GET /files/
│   │   ├── cad.py           # POST /CAD/viewer, DELETE /CAD/viewer
│   │   └── mfr.py           # POST /MFR/inference
│   ├── requirements.txt
│   └── README.md
├── mcp_server/
│   ├── server.py            # FastMCP — 3 tools
│   ├── pyproject.toml
│   └── README.md
└── README.md                # this file
```
