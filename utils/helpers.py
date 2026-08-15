"""Binary-string donusumleri, dogrulama ve resim format kontrolu."""

from __future__ import annotations

SUPPORTED_FORMATS = {"PNG", "BMP"}


def bytes_to_bits(data: bytes) -> str:
    """Byte dizisini '0101...' seklinde bit dizesine cevirir."""
    raise NotImplementedError


def bits_to_bytes(bits: str) -> bytes:
    """Bit dizesini ('0101...') byte dizisine cevirir."""
    raise NotImplementedError


def is_supported_image(image_path: str) -> bool:
    """Gorsel formatinin LSB gizleme icin uygun olup olmadigini kontrol eder (PNG/BMP gibi kayipsiz formatlar)."""
    raise NotImplementedError


def calculate_capacity(image_path: str) -> int:
    """Gorselin LSB ile gizleyebilecegi maksimum byte miktarini hesaplar."""
    raise NotImplementedError
