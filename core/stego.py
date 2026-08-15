"""LSB algoritmasi: bit manipulasyonu, encode/decode islemleri."""

from __future__ import annotations

import numpy as np
from PIL import Image

from core.exceptions import CapacityError, StegoDataError

LENGTH_HEADER_BITS = 32  # veri uzunlugunu tasiyan big-endian baslik boyutu (bit)
MAX_PAYLOAD_BYTES = 2**32 - 1  # 32-bit baslikla ifade edilebilecek azami veri boyutu


def _bytes_to_bits(data: bytes) -> np.ndarray:
    """Byte dizisini MSB-once sirali 0/1 bit dizisine cevirir."""
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def _bits_to_bytes(bits: np.ndarray) -> bytes:
    """MSB-once sirali 0/1 bit dizisini byte dizisine cevirir."""
    return np.packbits(bits).tobytes()


def encode(image_path: str, data: bytes, output_path: str) -> None:
    """Veriyi gorselin en dusuk anlamli bitlerine (LSB) gizler ve output_path'e PNG olarak yazar.

    Bit duzeni: once 32-bit big-endian uzunluk basligi (verinin byte cinsinden
    boyutu), ardindan verinin kendisi gelir. Bitler gorselin RGB kanallarinin
    duzlestirilmis byte dizisine sirayla, her byte'in en dusuk anlamli bitine
    gomulur (alfa kanali -- varsa -- saydamligin bozulmamasi icin kullanilmaz).
    """
    if len(data) > MAX_PAYLOAD_BYTES:
        raise CapacityError("Veri, 32-bit uzunluk basligiyla ifade edilemeyecek kadar buyuk")

    try:
        with Image.open(image_path) as img:
            image = img.convert("RGB")
    except OSError as exc:
        raise StegoDataError(f"Kapak gorseli acilamadi veya gecersiz: {image_path}") from exc

    pixels = np.array(image, dtype=np.uint8)
    flat = pixels.reshape(-1)

    header_bits = np.unpackbits(np.array([len(data)], dtype=">u4").view(np.uint8))
    payload_bits = _bytes_to_bits(data)
    all_bits = np.concatenate([header_bits, payload_bits])

    if all_bits.size > flat.size:
        raise CapacityError(
            f"Gorsel yetersiz kapasiteye sahip: {all_bits.size} bit gerekli, {flat.size} bit mevcut"
        )

    flat[: all_bits.size] = (flat[: all_bits.size] & 0xFE) | all_bits
    encoded_pixels = flat.reshape(pixels.shape)

    Image.fromarray(encoded_pixels, mode="RGB").save(output_path, format="PNG")


def decode(image_path: str) -> bytes:
    """Gorselin LSB'lerinden daha once gizlenmis veriyi cikarir.

    encode() tarafindan gomulen 32-bit big-endian uzunluk basligi + veri
    duzenini bekler. Okunan uzunluk gorselin tasiyabilecegi bit sayisini
    asiyorsa (bozuk veri veya hic veri gomulmemis gorsel) StegoDataError
    firlatir. Not: uzunluk basligi disinda bir butunluk isareti (checksum vb.)
    bulunmadigindan, hic veri gomulmemis bir gorsel de -- basligin dustugu
    LSB'ler rastgele kucuk bir deger olusturursa -- gecerliymis gibi
    algilanip anlamsiz bir sonuc dondurebilir; veri butunlugu ust katmanda
    (orn. crypto.decrypt'in HMAC dogrulamasi) saglanmalidir.
    """
    try:
        with Image.open(image_path) as img:
            image = img.convert("RGB")
    except OSError as exc:
        raise StegoDataError(f"Gorsel acilamadi veya gecersiz: {image_path}") from exc

    flat = np.array(image, dtype=np.uint8).reshape(-1)

    if flat.size < LENGTH_HEADER_BITS:
        raise StegoDataError("Gorsel, uzunluk basligini bile tasiyamayacak kadar kucuk")

    header_bits = (flat[:LENGTH_HEADER_BITS] & 1).astype(np.uint8)
    length = int(np.packbits(header_bits).view(">u4")[0])

    needed_bits = LENGTH_HEADER_BITS + length * 8
    if needed_bits > flat.size:
        raise StegoDataError("Gecersiz gizli veri basligi: uzunluk gorsel kapasitesini asiyor")

    payload_bits = (flat[LENGTH_HEADER_BITS:needed_bits] & 1).astype(np.uint8)
    return _bits_to_bytes(payload_bits)
