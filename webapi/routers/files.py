import core
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/files", tags=["File Management"])


@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    """Upload a CAD file.

    Returns a ``file_id`` (SHA-256 hash of the content).
    Uploading the same file again is idempotent — the same ``file_id`` is returned
    and the file is not re-stored (``already_existed`` will be ``true``).
    Pass the ``file_id`` to ``POST /CAD/viewer`` or ``POST /MFR/inference``
    instead of re-uploading the file each time.
    """
    try:
        file_id, path, existed = core.upload_CAD_file_persistent(file)
        return {
            "file_id": file_id,
            "filename": path.name,
            "already_existed": existed,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/")
def list_files():
    """List all CAD files currently stored on the server."""
    return {"files": core.list_persistent_CAD_files()}
