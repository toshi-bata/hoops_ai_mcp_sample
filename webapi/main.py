# Windows: switch to SelectorEventLoop before any imports to avoid a spurious
# KeyboardInterrupt caused by Proactor IPC pipes during pydantic schema generation.
import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
import pathlib

import core
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from routers import brep, cad, files, mfr


@asynccontextmanager
async def lifespan(app: FastAPI):
    core.CAD_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    core.CAD_VIEWER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    core.init_hoops_license()
    yield
    core.CAD_viewers.clear()
    core.CAD_face_colors.clear()


app = FastAPI(
    title="HOOPS AI WebAPI — minimal sample",
    description=(
        "Minimal FastAPI wrapper around HOOPS AI for file upload, "
        "CAD viewer, and MFR inference. For forum article use only."
    ),
    lifespan=lifespan,
)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


app.include_router(files.router)
app.include_router(cad.router)
app.include_router(mfr.router)
app.include_router(brep.router)

# Serve generated SCS / PNG files for the web viewer
core.CAD_VIEWER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/out", StaticFiles(directory=str(core.CAD_VIEWER_OUTPUT_DIR)), name="out")

# Serve HOOPS Web Viewer JS assets (place hoops-web-viewer-monolith.mjs here)
_static_dir = pathlib.Path(__file__).parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # Pre-warm pydantic schema generation before uvicorn's event loop starts.
    # On first run (no .pyc cache), slow compilation inside uvicorn's signal
    # handling window triggers a spurious KeyboardInterrupt on Windows.
    try:
        app.openapi()
    except Exception:
        pass

    uvicorn.run(app, host=args.host, port=args.port, reload=False)
