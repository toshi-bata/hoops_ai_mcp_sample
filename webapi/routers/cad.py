from typing import Optional

import core
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/CAD", tags=["CAD Viewer"])


def _session_id(request: Request) -> Optional[str]:
    return request.headers.get("X-Session-ID") or None


def _resolve_urls(result: dict, base_url: str) -> dict:
    """Convert relative /out/… and /CAD/… URLs to absolute ones."""
    for key in ("viewer_url", "image_url"):
        if result.get(key) and result[key].startswith("/"):
            result[key] = base_url.rstrip("/") + result[key]
    result.pop("_scs_filename", None)
    return result


@router.post("/viewer")
def open_viewer(
    request: Request,
    file: Optional[UploadFile] = File(None),
    file_id: Optional[str] = Query(None, description="file_id from POST /files/upload"),
):
    """Open a CAD file in the web viewer.

    Supply **either** ``file`` (multipart upload) **or** ``file_id`` (previously
    uploaded).  The ``X-Session-ID`` request header isolates viewer state so
    multiple clients can open viewers simultaneously without interfering.

    Returns ``viewer_url`` (browser-openable HTML page) and ``image_url``
    (PNG preview, if available).
    """
    try:
        if file_id:
            cad_path = core.find_persistent_CAD_file(file_id)
        elif file:
            _, cad_path, _ = core.upload_CAD_file_persistent(file)
        else:
            raise HTTPException(
                status_code=422,
                detail="Either 'file' or 'file_id' is required.",
            )
        result = core.create_CAD_viewer(cad_path, _session_id(request))
        return _resolve_urls(result, str(request.base_url))
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CAD viewer failed: {exc}") from exc


@router.delete("/viewer")
def close_viewer(request: Request, all: bool = Query(False)):
    """Terminate the CAD viewer for the current session.

    Pass ``?all=true`` to close all open viewers in the session.
    """
    try:
        return core.terminate_CAD_viewer(
            session_id=_session_id(request),
            terminate_all=all,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Terminate failed: {exc}") from exc


@router.get("/viewer/show", response_class=HTMLResponse)
def viewer_page(scs: str = Query(..., description="SCS filename in the out/ directory")):
    """Serve the HOOPS Web Viewer HTML page for the given SCS file."""
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HOOPS CAD Viewer</title>
  <style>
    html, body {{ margin: 0; padding: 0; overflow: hidden; }}
    #viewer {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; }}
    #legend {{
      position: fixed; top: 12px; right: 12px; z-index: 10;
      background: rgba(20,20,30,0.82); color: #f0f0f0;
      border-radius: 8px; padding: 10px 14px;
      font-family: sans-serif; font-size: 13px;
      max-height: calc(100vh - 30px); overflow-y: auto;
      backdrop-filter: blur(4px);
      display: none;
    }}
    #legend h4 {{ margin: 0 0 8px; font-size: 13px; color: #ccc; font-weight: 600; }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
    .legend-swatch {{
      width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0;
      border: 1px solid rgba(255,255,255,0.2);
    }}
  </style>
</head>
<body>
  <div id="viewer"></div>
  <div id="legend"><h4>Manufacturing Features</h4></div>
  <script type="module">
    import {{ WebViewer, Color }} from '/static/hoops-web-viewer-monolith.mjs';
    const scsFile = {repr(scs)};
    const hwv = new WebViewer({{
      container: document.getElementById('viewer'),
      endpointUri: '/out/' + scsFile,
    }});
    hwv.setCallbacks({{
      sceneReady: () => {{
        hwv.focusInput(true);
        window.addEventListener('resize', () => hwv.resizeCanvas());
        if (hwv.view.getAxisTriad) hwv.view.getAxisTriad().enable();
        if (hwv.view.getNavCube)  hwv.view.getNavCube().enable();
      }},
      modelStructureReady: async function () {{
        const res = await fetch('/CAD/viewer/colors?scs=' + scsFile);
        const data = await res.json();

        // Apply face colors
        if (data.colors && data.colors.length > 0) {{
          const model = hwv.model;
          const rootNode = model.getAbsoluteRootNode();
          const children = model.getNodeChildren(rootNode);
          if (children.length > 0) {{
            const modelNodeId = children[0];
            data.colors.forEach((rgb, faceId) => {{
              if (rgb) {{
                model.setNodeFaceColor(modelNodeId, faceId, new Color(rgb[0], rgb[1], rgb[2]));
              }}
            }});
          }}
        }}

        // Build legend
        if (data.color_map && Object.keys(data.color_map).length > 0) {{
          const legend = document.getElementById('legend');
          const entries = Object.values(data.color_map)
            .sort((a, b) => a.name.localeCompare(b.name));
          entries.forEach(entry => {{
            const [r, g, b] = entry.color_rgb;
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML =
              `<div class="legend-swatch" style="background:rgb(${{r}},${{g}},${{b}})"></div>` +
              `<span>${{entry.name.replace(/_/g, ' ')}}</span>`;
            legend.appendChild(item);
          }});
          legend.style.display = 'block';
        }}
      }},
    }});
    hwv.start();
  </script>
</body>
</html>""")


@router.get("/viewer/colors")
def viewer_colors(scs: str = Query(..., description="SCS filename")):
    """Return face color data and color map legend for the given SCS file (populated after MFR inference)."""
    return {
        "colors": core.CAD_face_colors.get(scs),
        "color_map": core.CAD_color_maps.get(scs),
    }
