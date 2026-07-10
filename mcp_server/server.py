"""
server.py — HOOPS AI MCP Server (minimal sample)

Exposes three MCP tools that Claude Desktop can call:
  - upload_cad_model      : upload a local CAD file → file_id
  - open_cad_viewer       : open the HOOPS Web Viewer for a CAD file
  - run_mfr_inference     : run Manufacturing Feature Recognition
"""

import os
import uuid
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = os.environ.get("HOOPS_WEBAPI_URL", "http://127.0.0.1:8000").rstrip("/")

# One unique session ID per MCP server process.
# All requests to the WebAPI carry this header so viewer state is isolated
# even when multiple Claude Desktop clients share the same WebAPI instance.
SESSION_ID = uuid.uuid4().hex
_SESSION_HEADERS = {"X-Session-ID": SESSION_ID}

mcp = FastMCP("HOOPS AI MCP Server (sample)")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _checked(response: httpx.Response) -> httpx.Response:
    """Raise RuntimeError with a descriptive message on non-2xx responses."""
    if not response.is_success:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"HTTP {response.status_code}: {detail}")
    return response


def _api_get(url: str, **kwargs) -> httpx.Response:
    try:
        return _checked(httpx.get(url, **kwargs))
    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc


def _api_post(url: str, **kwargs) -> httpx.Response:
    try:
        return _checked(httpx.post(url, **kwargs))
    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc


def _api_delete(url: str, **kwargs) -> httpx.Response:
    try:
        return _checked(httpx.delete(url, **kwargs))
    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc


# ---------------------------------------------------------------------------
# Shared helper: resolve file_id from path or existing id
# ---------------------------------------------------------------------------

def _resolve_file_id(cad_file_path: str = "", file_id: str = "") -> str:
    """Return a file_id, uploading the file first if only a path is given.

    This lets MCP tool callers pass a local path without worrying about the
    WebAPI's file_id-based interface — the MCP layer handles the translation.
    """
    if file_id:
        return file_id
    if cad_file_path:
        source = Path(cad_file_path).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"CAD file not found: {source}")
        with source.open("rb") as f:
            response = _api_post(
                f"{API_BASE}/files/upload",
                files={"file": (source.name, f, "application/octet-stream")},
                timeout=120,
            )
        return response.json()["file_id"]
    raise ValueError("Either cad_file_path or file_id must be provided.")


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def upload_cad_model(cad_file_path: str) -> dict:
    """Upload a local CAD file to the WebAPI and return its file_id.

    If the same file content was already uploaded the server returns the cached
    file_id without transferring the file again (SHA-256 deduplication).

    Use the returned file_id with open_cad_viewer or run_mfr_inference to avoid
    re-uploading the same model.

    Args:
        cad_file_path: Absolute or relative path to a CAD file
                       (.step, .stp, .iges, .igs, .x_t, .x_b, etc.).

    Returns:
        file_id, filename, already_existed
    """
    source = Path(cad_file_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"CAD file not found: {source}")
    with source.open("rb") as f:
        response = _api_post(
            f"{API_BASE}/files/upload",
            files={"file": (source.name, f, "application/octet-stream")},
            timeout=120,
        )
    return response.json()


@mcp.tool()
def open_cad_viewer(cad_file_path: str = "", file_id: str = "") -> dict:
    """Open a CAD file in the HOOPS Web Viewer and return the viewer URL.

    Call this tool ONLY when the user explicitly asks to open or display a
    viewer (e.g. "open the viewer", "show it in CADViewer").

    Provide either:
    - cad_file_path: local path to a CAD file (uploaded automatically)
    - file_id: ID from a previous upload_cad_model call (avoids re-upload)

    Args:
        cad_file_path: Local path to a CAD file (optional if file_id given).
        file_id: file_id from upload_cad_model (optional if path given).

    Returns:
        viewer_url (open in browser), image_url (PNG preview or null)
    """
    fid = _resolve_file_id(cad_file_path, file_id)
    response = _api_post(
        f"{API_BASE}/CAD/viewer",
        params={"file_id": fid},
        headers=_SESSION_HEADERS,
        timeout=120,
    )
    data = response.json()
    viewer_url = data.get("viewer_url")
    if not viewer_url:
        raise RuntimeError(f"viewer_url was not returned by the server: {data}")
    return {"viewer_url": viewer_url, "image_url": data.get("image_url")}


@mcp.tool()
def run_mfr_inference(cad_file_path: str = "", file_id: str = "") -> dict:
    """Run Manufacturing Feature Recognition (MFR) on a CAD file.

    Identifies per-face manufacturing features such as holes, slots, pockets,
    fillets, chamfers, etc. using a pre-trained graph neural network.

    Provide either:
    - cad_file_path: local path to a CAD file (uploaded automatically)
    - file_id: ID from a previous upload_cad_model call (avoids re-upload)

    Args:
        cad_file_path: Local path to a CAD file (optional if file_id given).
        file_id: file_id from upload_cad_model (optional if path given).

    Returns:
        predictions (per-face label IDs), probabilities, color_map
        (label → feature name + RGB), viewer_url, image_url
    """
    fid = _resolve_file_id(cad_file_path, file_id)
    response = _api_post(
        f"{API_BASE}/MFR/inference",
        params={"file_id": fid},
        headers=_SESSION_HEADERS,
        timeout=300,
    )
    return response.json()


@mcp.tool()
def get_brep_attributes(cad_file_path: str = "", file_id: str = "") -> dict:
    """Extract per-face and per-edge B-rep attributes from a CAD file.

    Retrieves geometric attributes for every face (type, area, centroid, loop
    count) and every edge (type, length, dihedral angle, convexity) in the
    B-rep model.

    Provide either:
    - cad_file_path: local path to a CAD file (uploaded automatically)
    - file_id: ID from a previous upload_cad_model call (avoids re-upload)

    Args:
        cad_file_path: Local path to a CAD file (optional if file_id given).
        file_id: file_id from upload_cad_model (optional if path given).

    Returns raw per-face and per-edge attribute data. Present it however best
    fits the user's request — as a table, a chart, a filtered/sorted list, or a
    summary — the response format is not fixed.
    """
    fid = _resolve_file_id(cad_file_path, file_id)
    response = _api_post(
        f"{API_BASE}/BRep/attributes",
        params={"file_id": fid},
        headers=_SESSION_HEADERS,
        timeout=120,
    )
    return response.json()


if __name__ == "__main__":
    mcp.run()
