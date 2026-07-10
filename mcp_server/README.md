# mcp_server — HOOPS AI MCP Server (minimal sample)

FastMCP server that lets Claude Desktop call HOOPS AI through four tools:

| Tool | Description |
|------|-------------|
| `upload_cad_model` | Upload a local CAD file; returns `file_id` |
| `open_cad_viewer` | Open the HOOPS Web Viewer for a CAD file |
| `run_mfr_inference` | Run Manufacturing Feature Recognition |
| `get_brep_attributes` | Extract per-face and per-edge B-rep attributes |

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- The WebAPI server running at `http://127.0.0.1:8000`
  (see `../webapi/README.md`)

## Setup

```bash
# Install dependencies with uv
cd mcp_server
uv sync

# Or with pip
pip install httpx "mcp[cli]"
```

## Register with Claude Desktop

Add the following entry to your `claude_desktop_config.json`
(location: `%APPDATA%\Claude\claude_desktop_config.json` on Windows,
`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

> **If using a plain Python venv instead of uv**, replace `"command": "uv"` and
> its `args` with the full path to the Python interpreter and `server.py`:
> ```json
> "command": "C:/path/to/.venv/Scripts/python.exe",
> "args": [
>   "C:/git/toshi-bata/HOOPS_AI/hoops_ai_mcp_sample/mcp_server/server.py"
> ]
> ```

## Environment variable

| Variable | Default | Description |
|----------|---------|-------------|
| `HOOPS_WEBAPI_URL` | `http://127.0.0.1:8000` | Base URL of the WebAPI server |

## Trying it out in Claude Desktop

1. Start the WebAPI server (see `../webapi/README.md`).
2. Restart Claude Desktop after editing `claude_desktop_config.json`.
3. In the chat, pass a local CAD file path, for example:

   > "Run MFR inference on C:/parts/bracket.step"

   Claude will call `upload_cad_model` and then `run_mfr_inference` automatically.
