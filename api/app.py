"""FastAPI uygulamasi: /api rotalarini ve statik frontend'i sunar.

CORSMiddleware bilerek eklenmedi: frontend ayni FastAPI orneginden (ayni origin)
sunuluyor, bu yuzden capacity/encode/decode fetch() cagrilari cross-origin degil.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from api.routes import router
from core.exceptions import CapacityError, DecryptionError, StegoCryptError, StegoDataError

# frontend/, calisma dizininden degil bu dosyanin konumundan cozumlenir; boylece
# uygulama repo kokunden farkli bir dizinden baslatilsa da statik dosyalar bulunur.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="StegoCrypt API")


def _error_response(exc: StegoCryptError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": exc.__class__.__name__},
    )


@app.exception_handler(CapacityError)
async def capacity_error_handler(request: Request, exc: CapacityError) -> JSONResponse:
    return _error_response(exc)


@app.exception_handler(DecryptionError)
async def decryption_error_handler(request: Request, exc: DecryptionError) -> JSONResponse:
    return _error_response(exc)


@app.exception_handler(StegoDataError)
async def stego_data_error_handler(request: Request, exc: StegoDataError) -> JSONResponse:
    return _error_response(exc)


@app.exception_handler(StegoCryptError)
async def stego_crypt_error_handler(request: Request, exc: StegoCryptError) -> JSONResponse:
    return _error_response(exc)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Beklenmeyen (StegoCryptError disi) hatalarda dahi API'nin kendi
    # {detail, error_type} sekli disina cikmayiz; hicbir zaman ham traceback
    # veya ic detay sizdirmayiz.
    return JSONResponse(
        status_code=500,
        content={"detail": "Beklenmeyen bir sunucu hatasi olustu.", "error_type": "InternalError"},
    )


app.include_router(router)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "index.html"))
