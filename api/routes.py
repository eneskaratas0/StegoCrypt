"""StegoCrypt web API rotalari: /api/capacity, /api/encode, /api/decode.

core.crypto, core.stego ve utils.helpers dogrudan sarilir (cli.py atlanir).
Yuklenen goruntuler ve cikti PNG'leri sadece bellekteki io.BytesIO nesnelerinde
tutulur; hicbir yere (diske, loga) goruntu, parola veya mesaj yazilmaz.
"""

from __future__ import annotations

import io

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import Response

from core import crypto, stego
from core.exceptions import CapacityError
from utils import helpers

router = APIRouter(prefix="/api")

# Bellekte arabellege alinacak azami yukleme/mesaj boyutu. Sunucu sadece
# localhost'a bagli olsa da, kaza sonucu asiri buyuk bir dosyanin bellegi
# tuketmesine karsi ucuz bir koruma.
MAX_IMAGE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_MESSAGE_BYTES = 1 * 1024 * 1024  # 1 MB


async def _read_upload(image: UploadFile) -> io.BytesIO:
    data = await image.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail=f"Gorsel cok buyuk (azami {MAX_IMAGE_BYTES} bayt).")
    return io.BytesIO(data)


@router.post("/capacity")
async def capacity(image: UploadFile) -> dict[str, int]:
    image_bytes = await _read_upload(image)
    capacity_bytes = helpers.calculate_capacity(image_bytes)
    return {"capacity_bytes": capacity_bytes}


@router.post("/encode")
async def encode(image: UploadFile, message: str = Form(...), password: str = Form(...)) -> Response:
    if len(message.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise HTTPException(status_code=413, detail=f"Mesaj cok buyuk (azami {MAX_MESSAGE_BYTES} bayt).")

    image_bytes = await _read_upload(image)

    capacity_bytes = helpers.calculate_capacity(image_bytes)
    image_bytes.seek(0)

    needed = crypto.encrypted_length(len(message.encode("utf-8")))
    if needed > capacity_bytes:
        raise CapacityError(
            f"Gorsel yetersiz kapasiteye sahip: sifrelenmis mesaj {needed} bayt, "
            f"gorsel en fazla {capacity_bytes} bayt tasiyabilir."
        )

    token = crypto.encrypt(message, password)

    output_buf = io.BytesIO()
    stego.encode(image_bytes, token, output_buf)

    return Response(
        content=output_buf.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="stego.png"'},
    )


@router.post("/decode")
async def decode(image: UploadFile, password: str = Form(...)) -> dict[str, str]:
    image_bytes = await _read_upload(image)
    token = stego.decode(image_bytes)
    message = crypto.decrypt(token, password)
    return {"message": message}
