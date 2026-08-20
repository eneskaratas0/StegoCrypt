"""LSB algoritmasi: bit manipulasyonu, encode/decode islemleri."""

from __future__ import annotations

import os
from typing import BinaryIO

import numpy as np
from PIL import Image

from core.exceptions import CapacityError, StegoDataError

LENGTH_HEADER_BITS = 32  # veri uzunlugunu tasiyan big-endian baslik boyutu (bit)
MAX_PAYLOAD_BYTES = 2**32 - 1  # 32-bit baslikla ifade edilebilecek azami veri boyutu

# Image.open/save (Pillow) dosya yolu, os.PathLike ve dosya-benzeri (BinaryIO,
# orn. io.BytesIO) nesneleri sorunsuz kabul eder; imzalar bunu yansitir.
ImageSource = str | os.PathLike[str] | BinaryIO

# Image.open, gecersiz/bozuk goruntülerde OSError disinda Exception'dan turetilmis
# DecompressionBombError da firlatabilir (asiri buyuk beyan edilmis piksel boyutu
# icin, gercek dosya kucuk olsa bile) -- her iki durumu da ayni sekilde ele aliriz.
IMAGE_OPEN_ERRORS = (OSError, Image.DecompressionBombError)


def describe_image_source(source: ImageSource) -> str:
    """Hata mesajlarinda gosterilecek kaynak tanimini uretir.

    Dosya yolu ise oldugu gibi, dosya-benzeri (orn. io.BytesIO -- API'de yuklenen
    goruntuler icin kullanilir) bir nesne ise Python repr'ini (bellek adresi vb.)
    disariya sizdirmamak icin genel bir aciklama dondurur.
    """
    if isinstance(source, (str, os.PathLike)):
        return str(source)
    return "yuklenen gorsel"


def _bytes_to_bits(data: bytes) -> np.ndarray:
    """Byte dizisini MSB-once sirali 0/1 bit dizisine cevirir."""
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def _bits_to_bytes(bits: np.ndarray) -> bytes:
    """MSB-once sirali 0/1 bit dizisini byte dizisine cevirir."""
    return np.packbits(bits).tobytes()


def encode(image_path: ImageSource, data: bytes, output_path: ImageSource) -> None:
    """Veriyi gorselin en dusuk anlamli bitlerine (LSB) gizler ve output_path'e PNG olarak yazar.

    Bit duzeni: once 32-bit big-endian uzunluk basligi (verinin byte cinsinden
    boyutu), ardindan verinin kendisi gelir. Bitler gorselin RGB kanallarinin
    duzlestirilmis byte dizisine sirayla, her byte'in en dusuk anlamli bitine
    gomulur (alfa kanali -- varsa -- saydamligin bozulmamasi icin kullanilmaz).

    image_path/output_path dosya yolu (str/os.PathLike) veya dosya-benzeri
    (orn. io.BytesIO) bir nesne olabilir -- Image.open/save ikisini de kabul eder.
    """
    if len(data) > MAX_PAYLOAD_BYTES:
        raise CapacityError("Veri, 32-bit uzunluk basligiyla ifade edilemeyecek kadar buyuk")

    try:
        with Image.open(image_path) as img:
            image = img.convert("RGB")
    except IMAGE_OPEN_ERRORS as exc:
        raise StegoDataError(f"Kapak gorseli acilamadi veya gecersiz: {describe_image_source(image_path)}") from exc

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

    try:
        Image.fromarray(encoded_pixels, mode="RGB").save(output_path, format="PNG")
    except OSError as exc:
        raise StegoDataError(f"Cikti gorseli yazilamadi: {describe_image_source(output_path)}") from exc


def decode(image_path: ImageSource) -> bytes:
    """Gorselin LSB'lerinden daha once gizlenmis veriyi cikarir.

    image_path dosya yolu (str/os.PathLike) veya dosya-benzeri (orn. io.BytesIO)
    bir nesne olabilir.

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
    except IMAGE_OPEN_ERRORS as exc:
        raise StegoDataError(f"Gorsel acilamadi veya gecersiz: {describe_image_source(image_path)}") from exc

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
