import numpy as np
import pytest
from PIL import Image

from core import stego
from core.exceptions import CapacityError, StegoDataError


def _make_image(path, width, height, mode="RGB", seed=0):
    rng = np.random.default_rng(seed)
    pixels = rng.integers(0, 256, size=(height, width, len(mode)), dtype=np.uint8)
    Image.fromarray(pixels, mode=mode).save(path, format="PNG")
    return path


def test_encode_decode_roundtrip(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.png"
    data = b"gizli mesaj: StegoCrypt 123"

    stego.encode(str(cover), data, str(output))
    result = stego.decode(str(output))

    assert result == data


def test_encode_decode_empty_data(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 16, 16)
    output = tmp_path / "stego.png"

    stego.encode(str(cover), b"", str(output))

    assert stego.decode(str(output)) == b""


def test_encode_output_is_lossless_png(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 16, 16)
    output = tmp_path / "stego.png"
    data = b"\x00\xff\x10\x20 binary veri \x00\x01"

    stego.encode(str(cover), data, str(output))

    with Image.open(output) as img:
        assert img.format == "PNG"

    assert stego.decode(str(output)) == data


def test_encode_decode_roundtrip_with_non_rgb_input(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 16, 16, mode="RGBA")
    output = tmp_path / "stego.png"
    data = b"rgba kapak gorseli"

    stego.encode(str(cover), data, str(output))

    assert stego.decode(str(output)) == data


def test_encode_with_insufficient_capacity_raises(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 4, 4)  # 4*4*3 = 48 bit kapasite
    output = tmp_path / "stego.png"
    data = b"bu veri kesinlikle 4x4 gorsele sigmaz, cok uzun bir mesaj"

    with pytest.raises(CapacityError):
        stego.encode(str(cover), data, str(output))

    assert not output.exists()


def test_decode_image_too_small_for_header_raises(tmp_path):
    # 1x1 RGB = 3 bit, 32-bit uzunluk basligini bile tasiyamaz
    cover = _make_image(tmp_path / "tiny.png", 1, 1)

    with pytest.raises(StegoDataError):
        stego.decode(str(cover))


def test_encode_decode_at_exact_capacity_boundary(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 4, 4)  # 4*4*3 = 48 bit kapasite
    output = tmp_path / "stego.png"
    # 32 bit baslik + 2 byte (16 bit) veri = 48 bit: kapasiteyi tam doldurur.
    data = b"ab"

    stego.encode(str(cover), data, str(output))

    assert stego.decode(str(output)) == data


def test_decode_nonexistent_file_raises(tmp_path):
    with pytest.raises(StegoDataError):
        stego.decode(str(tmp_path / "olmayan.png"))


def test_decode_non_image_file_raises(tmp_path):
    path = tmp_path / "not_an_image.png"
    path.write_bytes(b"bu bir PNG dosyasi degil, duz metin")

    with pytest.raises(StegoDataError):
        stego.decode(str(path))


def test_encode_with_nonexistent_cover_image_raises(tmp_path):
    with pytest.raises(StegoDataError):
        stego.encode(str(tmp_path / "olmayan.png"), b"veri", str(tmp_path / "out.png"))


def test_decode_image_without_embedded_data_raises(tmp_path):
    path = tmp_path / "garbage_header.png"
    pixels = np.zeros((4, 4, 3), dtype=np.uint8)
    # Ilk 32 bitin LSB'lerini 1 yaparak gorselin tasiyabileceginden
    # cok daha buyuk bir uzunluk basligi (0xFFFFFFFF) uretiyoruz.
    flat = pixels.reshape(-1)
    flat[:32] |= 1
    Image.fromarray(pixels, mode="RGB").save(path, format="PNG")

    with pytest.raises(StegoDataError):
        stego.decode(str(path))
