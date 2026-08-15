"""LSB algoritmasi: bit manipulasyonu, encode/decode islemleri."""

from __future__ import annotations


def encode(image_path: str, data: bytes, output_path: str) -> None:
    """Veriyi gorselin en dusuk anlamli bitlerine (LSB) gizler ve output_path'e yazar."""
    raise NotImplementedError


def decode(image_path: str) -> bytes:
    """Gorselin LSB'lerinden daha once gizlenmis veriyi cikarir."""
    raise NotImplementedError
