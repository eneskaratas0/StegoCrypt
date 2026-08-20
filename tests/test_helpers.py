import io

import numpy as np
import pytest
from PIL import Image

from core import stego
from core.exceptions import CapacityError, StegoDataError
from core.stego import LENGTH_HEADER_BITS
from utils import helpers


def _make_image(path, width, height, mode="RGB", seed=0):
    rng = np.random.default_rng(seed)
    pixels = rng.integers(0, 256, size=(height, width, len(mode)), dtype=np.uint8)
    Image.fromarray(pixels, mode=mode).save(path, format="PNG")
    return path


def test_calculate_capacity_matches_formula(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 10, 4)
    expected = (10 * 4 * 3 - LENGTH_HEADER_BITS) // 8

    assert helpers.calculate_capacity(str(cover)) == expected


def test_calculate_capacity_matches_actual_stego_boundary(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 4, 4)  # 48 bit kapasite
    output = tmp_path / "out.png"
    capacity = helpers.calculate_capacity(str(cover))

    stego.encode(str(cover), bytes(capacity), str(output))

    with pytest.raises(CapacityError):
        stego.encode(str(cover), bytes(capacity + 1), str(output))


def test_calculate_capacity_ignores_alpha_channel(tmp_path):
    cover_rgb = _make_image(tmp_path / "rgb.png", 8, 8, mode="RGB")
    cover_rgba = _make_image(tmp_path / "rgba.png", 8, 8, mode="RGBA")

    assert helpers.calculate_capacity(str(cover_rgb)) == helpers.calculate_capacity(str(cover_rgba))


def test_calculate_capacity_with_file_like_object(tmp_path):
    cover = _make_image(tmp_path / "cover.png", 10, 4)
    buffer = io.BytesIO(cover.read_bytes())

    assert helpers.calculate_capacity(buffer) == helpers.calculate_capacity(str(cover))


def test_calculate_capacity_with_nonexistent_image_raises(tmp_path):
    with pytest.raises(StegoDataError):
        helpers.calculate_capacity(str(tmp_path / "olmayan.png"))


def test_calculate_capacity_with_non_image_file_raises(tmp_path):
    path = tmp_path / "not_an_image.png"
    path.write_bytes(b"bu bir PNG dosyasi degil")

    with pytest.raises(StegoDataError):
        helpers.calculate_capacity(str(path))
