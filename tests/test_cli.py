import numpy as np
import pytest
from PIL import Image

import cli
from cli import main
from core import crypto
from core.stego import LENGTH_HEADER_BITS


def _make_image(path, width, height, mode="RGB", seed=0):
    rng = np.random.default_rng(seed)
    pixels = rng.integers(0, 256, size=(height, width, len(mode)), dtype=np.uint8)
    Image.fromarray(pixels, mode=mode).save(path, format="PNG")
    return path


def _run(monkeypatch, argv):
    monkeypatch.setattr("sys.argv", ["stegocrypt", *argv])
    main()


def test_encode_decode_roundtrip(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.png"

    _run(
        monkeypatch,
        [
            "encode",
            "--image", str(cover),
            "--message", "gizli mesaj: StegoCrypt 123",
            "--output", str(output),
            "--password", "guclu-parola",
        ],
    )
    encode_out = capsys.readouterr().out
    assert str(output) in encode_out

    _run(
        monkeypatch,
        [
            "decode",
            "--image", str(output),
            "--password", "guclu-parola",
        ],
    )
    decode_out = capsys.readouterr().out
    assert decode_out.strip() == "gizli mesaj: StegoCrypt 123"


def test_decode_with_wrong_password_exits_nonzero(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.png"

    _run(
        monkeypatch,
        [
            "encode",
            "--image", str(cover),
            "--message", "gizli veri",
            "--output", str(output),
            "--password", "dogru-parola",
        ],
    )
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc_info:
        _run(
            monkeypatch,
            [
                "decode",
                "--image", str(output),
                "--password", "yanlis-parola",
            ],
        )

    assert exc_info.value.code == 1
    assert "Hata" in capsys.readouterr().err


def test_encode_with_insufficient_capacity_exits_nonzero(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 4, 4)  # 48 bit kapasite
    output = tmp_path / "stego.png"

    with pytest.raises(SystemExit) as exc_info:
        _run(
            monkeypatch,
            [
                "encode",
                "--image", str(cover),
                "--message", "bu mesaj kesinlikle 4x4 gorsele sigmayacak kadar uzun",
                "--output", str(output),
                "--password", "parola",
            ],
        )

    assert exc_info.value.code == 1
    assert "Hata" in capsys.readouterr().err
    assert not output.exists()


def test_encode_with_unwritable_output_exits_nonzero(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "olmayan_dizin" / "stego.png"

    with pytest.raises(SystemExit) as exc_info:
        _run(
            monkeypatch,
            [
                "encode",
                "--image", str(cover),
                "--message", "gizli veri",
                "--output", str(output),
                "--password", "parola",
            ],
        )

    assert exc_info.value.code == 1
    assert "Hata" in capsys.readouterr().err


def test_decode_non_image_file_exits_nonzero(tmp_path, monkeypatch, capsys):
    path = tmp_path / "not_an_image.png"
    path.write_bytes(b"bu bir PNG dosyasi degil, duz metin")

    with pytest.raises(SystemExit) as exc_info:
        _run(
            monkeypatch,
            [
                "decode",
                "--image", str(path),
                "--password", "parola",
            ],
        )

    assert exc_info.value.code == 1
    assert "Hata" in capsys.readouterr().err


def test_encode_decode_prompts_for_message_and_password_when_omitted(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.png"

    monkeypatch.setattr("builtins.input", lambda prompt="": "prompt ile girilen mesaj")
    encode_passwords = iter(["gizli-parola", "gizli-parola"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(encode_passwords))

    _run(monkeypatch, ["encode", "--image", str(cover), "--output", str(output)])
    capsys.readouterr()

    monkeypatch.setattr("getpass.getpass", lambda prompt="": "gizli-parola")
    _run(monkeypatch, ["decode", "--image", str(output)])

    assert capsys.readouterr().out.strip() == "prompt ile girilen mesaj"


def test_encode_with_nonexistent_cover_image_exits_nonzero(tmp_path, monkeypatch, capsys):
    output = tmp_path / "stego.png"

    with pytest.raises(SystemExit) as exc_info:
        _run(
            monkeypatch,
            [
                "encode",
                "--image", str(tmp_path / "olmayan.png"),
                "--message", "gizli veri",
                "--output", str(output),
                "--password", "parola",
            ],
        )

    assert exc_info.value.code == 1
    assert "Hata" in capsys.readouterr().err
    assert not output.exists()


def test_encode_decode_at_exact_capacity_boundary(tmp_path, monkeypatch, capsys):
    message = "ab"
    password = "parola"
    # Sifreleme sonrasi gercek token uzunlugunu (salt+iv+ciphertext+mac) hesaba
    # katarak, kapak goruntusunun kapasitesini token'i tam tam dolduracak sekilde
    # boyutlandiriyoruz (RGB -> 3 bit/piksel).
    needed_bits = LENGTH_HEADER_BITS + len(crypto.encrypt(message, password)) * 8
    width = -(-needed_bits // 3)  # yukari yuvarlama
    cover = _make_image(tmp_path / "cover.png", width, 1)
    output = tmp_path / "stego.png"

    _run(
        monkeypatch,
        [
            "encode",
            "--image", str(cover),
            "--message", message,
            "--output", str(output),
            "--password", password,
        ],
    )
    capsys.readouterr()

    _run(monkeypatch, ["decode", "--image", str(output), "--password", password])

    assert capsys.readouterr().out.strip() == message


def test_encode_decode_roundtrip_unicode_message(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.png"
    message = "parola öğrenmek 🔒 çok önemli"

    _run(
        monkeypatch,
        [
            "encode",
            "--image", str(cover),
            "--message", message,
            "--output", str(output),
            "--password", "parola",
        ],
    )
    capsys.readouterr()

    _run(monkeypatch, ["decode", "--image", str(output), "--password", "parola"])

    assert capsys.readouterr().out.strip() == message


def test_encode_with_non_png_output_exits_nonzero(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.jpg"

    with pytest.raises(SystemExit) as exc_info:
        _run(
            monkeypatch,
            [
                "encode",
                "--image", str(cover),
                "--message", "gizli veri",
                "--output", str(output),
                "--password", "parola",
            ],
        )

    assert exc_info.value.code == 1
    assert ".png" in capsys.readouterr().err
    assert not output.exists()


def test_encode_with_mismatched_password_confirmation_exits_nonzero(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.png"

    monkeypatch.setattr("builtins.input", lambda prompt="": "mesaj")
    mismatched_passwords = iter(["parola-bir", "parola-iki"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(mismatched_passwords))

    with pytest.raises(SystemExit) as exc_info:
        _run(monkeypatch, ["encode", "--image", str(cover), "--output", str(output)])

    assert exc_info.value.code == 1
    assert "eslesmiyor" in capsys.readouterr().err
    assert not output.exists()


def test_main_handles_unexpected_exception_gracefully(tmp_path, monkeypatch, capsys):
    cover = _make_image(tmp_path / "cover.png", 32, 32)
    output = tmp_path / "stego.png"

    def _boom(*args, **kwargs):
        raise RuntimeError("beklenmeyen hata simulasyonu")

    monkeypatch.setattr(cli.crypto, "encrypt", _boom)

    with pytest.raises(SystemExit) as exc_info:
        _run(
            monkeypatch,
            [
                "encode",
                "--image", str(cover),
                "--message", "gizli veri",
                "--output", str(output),
                "--password", "parola",
            ],
        )

    assert exc_info.value.code == 1
    assert "Beklenmeyen hata" in capsys.readouterr().err
    assert not output.exists()
