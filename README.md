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
mcp_server/server.py   — FastMCP, 4 MCP tools
    │  HTTP (httpx)
    ▼
webapi/main.py         — FastAPI, 4 endpoint groups
    │  Python API
    ▼
HOOPS AI SDK           — CAD loading / SCS export / MFR inference
```

Four feature groups are implemented:

| Feature | WebAPI endpoint | MCP tool |
|---------|-----------------|----------|
| File upload | `POST /files/upload` | `upload_cad_model` |
| CAD viewer | `POST /CAD/viewer` | `open_cad_viewer` |
| MFR inference | `POST /MFR/inference` | `run_mfr_inference` |
| BRep attributes | `POST /BRep/attributes` | `get_brep_attributes` |

> No sample CAD files are included. Try it with your own 3D CAD files.

---

## Getting started

1. Set up the WebAPI server → see [`webapi/README.md`](webapi/README.md)
2. Register the MCP server with Claude Desktop → see [`mcp_server/README.md`](mcp_server/README.md)

---

## Repository layout

```
hoops_ai_mcp_sample/
├── webapi/
│   ├── main.py              # FastAPI app — license init via lifespan
│   ├── core.py              # file_id management, CAD viewer, MFR inference, BRep attributes
│   ├── routers/
│   │   ├── files.py         # POST /files/upload, GET /files/
│   │   ├── cad.py           # POST /CAD/viewer, DELETE /CAD/viewer
│   │   ├── mfr.py           # POST /MFR/inference
│   │   └── brep.py          # POST /BRep/attributes
│   ├── static/              # place hoops-web-viewer-monolith.mjs here (not tracked)
│   ├── requirements.txt
│   └── README.md            # WebAPI setup
├── mcp_server/
│   ├── server.py            # FastMCP — 4 tools
│   ├── pyproject.toml
│   └── README.md            # MCP server setup
└── README.md                # this file
```
