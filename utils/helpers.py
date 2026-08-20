"""Gorsel kapasite hesaplama yardimci fonksiyonu."""

from __future__ import annotations

from PIL import Image

from core.exceptions import StegoDataError
from core.stego import LENGTH_HEADER_BITS, ImageSource


def calculate_capacity(image_path: ImageSource) -> int:
    """Gorselin LSB ile gizleyebilecegi maksimum byte miktarini hesaplar.

    core.stego.encode ile ayni piksel-bit yerlesimini esas alir: sadece RGB
    kanallari (alfa haric) kullanilir ve 32-bit uzunluk basligi icin ayrilan
    yer dusulur. image_path dosya yolu (str/os.PathLike) veya dosya-benzeri
    (orn. io.BytesIO) bir nesne olabilir.
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except OSError as exc:
        raise StegoDataError(f"Gorsel acilamadi veya gecersiz: {image_path}") from exc

    total_bits = width * height * 3
    payload_bits = total_bits - LENGTH_HEADER_BITS
    return max(payload_bits, 0) // 8
