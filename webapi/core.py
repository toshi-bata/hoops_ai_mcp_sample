"""
core.py — HOOPS AI WebAPI (minimal sample)

Handles:
  - License initialization (once at startup)
  - Persistent CAD file upload (SHA-256 deduplication)
  - CAD viewer creation / termination  (session-isolated)
  - MFR inference (model cached after first load)
"""

import hashlib
import logging
import os
import pathlib
import uuid
from typing import Any, Optional

import numpy as np
from fastapi import UploadFile

logger = logging.getLogger(__name__)

APP_ROOT = pathlib.Path(__file__).resolve().parent
CAD_UPLOAD_DIR = APP_ROOT / "uploads"
CAD_VIEWER_OUTPUT_DIR = APP_ROOT / "out"

# Module-level state (one process, one server)
MFR_inference_model = None
CAD_viewers: dict[str, dict[str, Any]] = {}  # session_id -> {file_key -> viewer_info}
CAD_face_colors: dict[str, list] = {}         # scs_filename -> [[r,g,b], ...]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def json_safe(obj: Any) -> Any:
    """Recursively convert numpy types to JSON-serialisable Python types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    return obj


def _load_env() -> None:
    """Load .env from the webapi directory if present."""
    env_path = APP_ROOT / ".env"
    if not env_path.exists():
        return
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            "Add it to webapi/.env."
        )
    return value


# ---------------------------------------------------------------------------
# License
# ---------------------------------------------------------------------------

def init_hoops_license() -> None:
    """Initialize the HOOPS AI license. Called once via FastAPI lifespan."""
    import hoops_ai

    _load_env()
    license_key = _get_required_env("HOOPS_AI_LICENSE")
    hoops_ai.set_license(license_key, validate=True)
    logger.info("HOOPS AI license initialized.")


# ---------------------------------------------------------------------------
# Persistent file storage  (SHA-256 deduplication)
# ---------------------------------------------------------------------------

def upload_CAD_file_persistent(upload_file: UploadFile) -> tuple[str, pathlib.Path, bool]:
    """Store an uploaded CAD file keyed by SHA-256 hash.

    Returns (file_id, dest_path, already_existed).
    Uploading identical content twice returns the same file_id without re-writing.
    """
    if not upload_file.filename:
        raise RuntimeError("Uploaded file must have a filename.")

    data = upload_file.file.read()
    file_id = hashlib.sha256(data).hexdigest()
    safe_name = pathlib.PurePath(upload_file.filename).name

    CAD_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = CAD_UPLOAD_DIR / f"{file_id}_{safe_name}"
    existed = dest.exists()
    if not existed:
        dest.write_bytes(data)
    return file_id, dest, existed


def find_persistent_CAD_file(file_id: str) -> pathlib.Path:
    """Resolve a file_id to its path on disk. Raises RuntimeError if not found."""
    matches = list(CAD_UPLOAD_DIR.glob(f"{file_id}_*"))
    if not matches:
        raise RuntimeError(
            f"No file found for file_id='{file_id}'. "
            "Upload the file first via POST /files/upload."
        )
    return matches[0]


def list_persistent_CAD_files() -> list[dict]:
    """Return metadata for all uploaded files."""
    if not CAD_UPLOAD_DIR.exists():
        return []
    result = []
    for p in sorted(CAD_UPLOAD_DIR.iterdir()):
        if p.is_file():
            parts = p.name.split("_", 1)
            result.append({
                "file_id": parts[0],
                "filename": parts[1] if len(parts) > 1 else p.name,
                "size_bytes": p.stat().st_size,
            })
    return result


# ---------------------------------------------------------------------------
# CAD Viewer
# ---------------------------------------------------------------------------

def create_CAD_viewer(
    cad_file_path: pathlib.Path,
    session_id: Optional[str] = None,
) -> dict[str, Any]:
    """Export a CAD file as an SCS stream-cache and return URLs for the web viewer.

    session_id isolates state so multiple clients can open viewers simultaneously
    without colliding.  Within the same session, the same source file is cached
    (SCS is not regenerated on every call).
    """
    from hoops_ai.cadaccess import HOOPSLoader, HOOPSTools

    CAD_VIEWER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_key = str(cad_file_path.resolve())
    track_key = session_id or ""
    session_viewers = CAD_viewers.setdefault(track_key, {})

    # Return cached SCS when the same file is already open in this session
    if session_id:
        existing = session_viewers.get(file_key)
        if existing:
            scs_path = CAD_VIEWER_OUTPUT_DIR / existing["scs_filename"]
            if scs_path.exists():
                png_url = (
                    f"/out/{existing['png_filename']}"
                    if existing.get("png_filename")
                    else None
                )
                return {
                    "viewer_url": f"/CAD/viewer/show?scs={scs_path.name}",
                    "image_url": png_url,
                    "_scs_filename": scs_path.name,
                }

    # UUID prefix ensures no filename collisions across sessions
    unique_id = uuid.uuid4().hex[:12]
    scs_name = f"{unique_id}_{cad_file_path.stem}.scs"
    scs_out = CAD_VIEWER_OUTPUT_DIR / scs_name

    cad_loader = HOOPSLoader()
    model = cad_loader.create_from_file(str(cad_file_path))

    tools = HOOPSTools()
    png_path, scs_path = tools.exportStreamCache(
        model,
        filename=str(scs_out),
        is_white_background=True,
        overwrite=True,
    )
    scs_path = pathlib.Path(scs_path)
    png_path = pathlib.Path(png_path) if png_path else None

    png_filename = png_path.name if png_path and png_path.exists() else None
    session_viewers[file_key] = {
        "scs_filename": scs_path.name,
        "png_filename": png_filename,
    }

    return {
        "viewer_url": f"/CAD/viewer/show?scs={scs_path.name}",
        "image_url": f"/out/{png_filename}" if png_filename else None,
        "_scs_filename": scs_path.name,
    }


def terminate_CAD_viewer(
    session_id: Optional[str] = None,
    terminate_all: bool = False,
) -> dict[str, Any]:
    """Delete SCS/PNG files and clear viewer state for the given session."""
    session_viewers = CAD_viewers.get(session_id or "", {})

    def _delete_files(info: dict) -> None:
        for key in ("scs_filename", "png_filename"):
            fname = info.get(key)
            if fname:
                (CAD_VIEWER_OUTPUT_DIR / fname).unlink(missing_ok=True)
        scs = info.get("scs_filename")
        if scs:
            CAD_face_colors.pop(scs, None)

    if terminate_all:
        count = len(session_viewers)
        for info in session_viewers.values():
            _delete_files(info)
        session_viewers.clear()
        return {"terminated": count}

    if not session_viewers:
        raise RuntimeError("No active CAD viewer for this session.")

    file_key = next(reversed(session_viewers))
    _delete_files(session_viewers[file_key])
    del session_viewers[file_key]
    return {"terminated": 1}


# ---------------------------------------------------------------------------
# MFR Inference
# ---------------------------------------------------------------------------

def _get_MFR_inference_model():
    """Load the MFR model once and cache it at module level."""
    global MFR_inference_model
    if MFR_inference_model is not None:
        return MFR_inference_model

    from hoops_ai.cadaccess import HOOPSLoader
    from hoops_ai.ml.EXPERIMENTAL import FlowInference, GraphNodeClassification

    _load_env()
    notebooks_dir = pathlib.Path(_get_required_env("HOOPS_AI_NOTEBOOK_DIR"))
    model_name = _get_required_env("HOOPS_AI_MFR_MODEL_NAME")
    trained_model = notebooks_dir.parent / "packages" / "trained_ml_models" / model_name
    if not trained_model.exists():
        raise RuntimeError(
            f"MFR model checkpoint not found: {trained_model}. "
            "Check HOOPS_AI_MFR_MODEL_NAME in .env."
        )

    output_dir = notebooks_dir / "out"
    output_dir.mkdir(parents=True, exist_ok=True)

    loader = HOOPSLoader()
    flow = FlowInference(
        cad_loader=loader,
        flowmodel=GraphNodeClassification(result_dir=str(output_dir)),
    )
    flow.load_from_checkpoint(trained_model)
    MFR_inference_model = flow
    logger.info("MFR inference model loaded and cached.")
    return MFR_inference_model


def run_MFR_inference(
    cad_file_path: pathlib.Path,
    session_id: Optional[str] = None,
) -> dict[str, Any]:
    """Run per-face manufacturing feature recognition on a CAD file.

    Returns predictions (per-face label IDs), probabilities, viewer_url,
    image_url (both best-effort), and a color_map for the present labels.
    """
    from hoops_ai.insights.utils import ColorPalette

    model = _get_MFR_inference_model()
    ml_input = model.preprocess(str(cad_file_path))
    predictions, probabilities = model.predict_and_postprocess(ml_input)

    session_preds = json_safe(predictions)

    viewer_url = None
    image_url = None
    scs_filename = None
    try:
        viewer_result = create_CAD_viewer(cad_file_path, session_id)
        viewer_url = viewer_result.get("viewer_url")
        image_url = viewer_result.get("image_url")
        scs_filename = viewer_result.get("_scs_filename")
    except Exception:
        pass  # Viewer is best-effort; inference result is returned regardless

    # Build per-face color list and a label-level color legend
    _load_env()
    labels_description = _get_mfr_labels_description()
    color_palette = ColorPalette.from_labels(
        labels_description,
        reserved_colors={0: (200, 200, 200)},
    )

    face_colors: list[list[int]] = []
    for label_id in session_preds:
        rgb = color_palette.get_color(int(label_id))
        face_colors.append([int(rgb[0]), int(rgb[1]), int(rgb[2])])

    if scs_filename:
        CAD_face_colors[scs_filename] = face_colors

    present_ids = {int(lid) for lid in session_preds}
    color_map = {
        str(lid): {
            "name": info["name"] if isinstance(info, dict) else info,
            "color_rgb": list(color_palette.get_color(lid)),
        }
        for lid, info in labels_description.items()
        if int(lid) in present_ids
    }

    return {
        "predictions": json_safe(predictions),
        "probabilities": json_safe(probabilities),
        "viewer_url": viewer_url,
        "image_url": image_url,
        "color_map": color_map,
    }


def _get_mfr_labels_description() -> dict:
    """Load MFR label descriptions bundled with the server."""
    labels_path = pathlib.Path(__file__).parent / "data" / "mfr_labels_description.json"
    import json
    with labels_path.open() as f:
        raw = json.load(f)
    # Keys may be strings; normalise to int
    return {int(k): v for k, v in raw.items()}
