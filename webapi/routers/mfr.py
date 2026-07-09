from typing import Optional

import core
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile

router = APIRouter(prefix="/MFR", tags=["MFR"])


def _session_id(request: Request) -> Optional[str]:
    return request.headers.get("X-Session-ID") or None


@router.post("/inference")
def mfr_inference(
    request: Request,
    file: Optional[UploadFile] = File(None),
    file_id: Optional[str] = Query(None, description="file_id from POST /files/upload"),
):
    """Run Manufacturing Feature Recognition (MFR) on a CAD file.

    Supply **either** ``file`` (multipart upload) **or** ``file_id``
    (previously uploaded).  ``X-Session-ID`` is used to associate the generated
    viewer with the calling client's session.

    Returns per-face ``predictions`` (label IDs), ``probabilities``, a
    ``color_map`` (label ID → feature name + RGB), and ``viewer_url`` /
    ``image_url`` (best-effort; ``null`` if viewer generation fails).
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
        result = core.run_MFR_inference(cad_path, _session_id(request))
        # Convert relative URLs to absolute
        base = str(request.base_url).rstrip("/")
        for key in ("viewer_url", "image_url"):
            if result.get(key) and result[key].startswith("/"):
                result[key] = base + result[key]
        result.pop("_scs_filename", None)
        return result
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"MFR inference failed: {exc}") from exc
