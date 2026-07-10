from typing import Optional

import core
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

router = APIRouter(prefix="/BRep", tags=["BRep"])


@router.post("/attributes")
def brep_attributes(
    file: Optional[UploadFile] = File(None),
    file_id: Optional[str] = Query(None, description="file_id from POST /files/upload"),
):
    """Extract face and edge attributes from the B-rep model of a CAD file.

    Supply **either** ``file`` (multipart upload) **or** ``file_id``
    (previously uploaded).  No session header is required — this is a
    stateless, read-only operation that does not interact with the viewer.

    Returns per-face ``types``, ``areas``, ``centroids``, ``loops``, and
    per-edge ``types``, ``lengths``, ``dihedrals``, ``convexities``, along
    with human-readable ``types_description`` dicts for both faces and edges.
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
        return core.get_brep_attributes(cad_path)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"BRep attribute extraction failed: {exc}") from exc
