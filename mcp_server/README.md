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
- The WebAPI server running and accessible from this machine
  (see `../webapi/README.md`)
  - Same machine: `http://127.0.0.1:8000`
  - Remote server: `http://<server-ip-or-hostname>:8000`

## Setup

```bash
# Install dependencies with uv
cd mcp_server
uv sync

# Or with pip
pip install httpx "mcp[cli]"
```

## Register with Claude Desktop

Edit `claude_desktop_config.json` and add the following entry under `mcpServers`:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Windows:**
```json
{
  "mcpServers": {
    "hoops-ai-sample": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\hoops_ai_mcp_sample\\mcp_server",
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

**Linux / macOS:**
```json
{
  "mcpServers": {
    "hoops-ai-sample": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/hoops_ai_mcp_sample/mcp_server",
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

> For a remote WebAPI server, replace `http://127.0.0.1:8000` with `http://<server-ip-or-hostname>:8000`.

> **Troubleshooting — `uv` not found:** Claude Desktop launches with a limited PATH and may fail to find `uv` even if it works in your terminal.
> If the MCP server does not appear in Claude Desktop, use the **full path** to `uv` instead of `"uv"`:
>
> **Windows:**
> ```powershell
> where.exe uv   # e.g. C:\Users\<you>\.local\bin\uv.exe
> ```
>
> **Linux / macOS:**
> ```bash
> which uv   # e.g. /home/<you>/.local/bin/uv
> ```
>
> Then update `"command"` in the config with the full path found above.

> **If using a plain Python venv instead of uv**, replace `"command": "uv"` and
> its `args` with the full path to the Python interpreter and `server.py`:
>
> **Windows:**
> ```json
> "command": "C:/path/to/.venv/Scripts/python.exe",
> "args": ["C:/path/to/hoops_ai_mcp_sample/mcp_server/server.py"]
> ```
>
> **Linux / macOS:**
> ```json
> "command": "/path/to/.venv/bin/python",
> "args": ["/path/to/hoops_ai_mcp_sample/mcp_server/server.py"]
> ```

## Trying it out in Claude Desktop

1. Start the WebAPI server (see `../webapi/README.md`).
2. Restart Claude Desktop after editing `claude_desktop_config.json`.
3. In the chat, pass a local CAD file path, for example:

   > "Run MFR inference on C:/parts/bracket.step"

   Claude will call `upload_cad_model` and then `run_mfr_inference` automatically.
