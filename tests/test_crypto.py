import os

import pytest

from core import crypto
from core.exceptions import DecryptionError


def test_encrypt_decrypt_roundtrip():
    plaintext = "gizli mesaj: StegoCrypt 123"
    password = "guclu-parola"

    token = crypto.encrypt(plaintext, password)
    result = crypto.decrypt(token, password)

    assert result == plaintext


def test_encrypt_output_is_randomized():
    token_a = crypto.encrypt("ayni mesaj", "parola")
    token_b = crypto.encrypt("ayni mesaj", "parola")

    assert token_a != token_b  # rastgele salt/iv nedeniyle


def test_decrypt_with_wrong_password_raises():
    token = crypto.encrypt("gizli veri", "dogru-parola")

    with pytest.raises(DecryptionError):
        crypto.decrypt(token, "yanlis-parola")


def test_decrypt_with_truncated_token_raises():
    with pytest.raises(DecryptionError):
        crypto.decrypt(b"cok-kisa", "parola")


def test_decrypt_with_tampered_ciphertext_raises():
    token = bytearray(crypto.encrypt("gizli veri", "parola"))
    token[-(crypto.MAC_SIZE + 1)] ^= 0xFF  # ciphertext'in son byte'ini boz

    with pytest.raises(DecryptionError):
        crypto.decrypt(bytes(token), "parola")


def test_decrypt_with_tampered_mac_raises():
    token = bytearray(crypto.encrypt("gizli veri", "parola"))
    token[-1] ^= 0xFF  # MAC'in son byte'ini boz

    with pytest.raises(DecryptionError):
        crypto.decrypt(bytes(token), "parola")


def test_encrypt_decrypt_empty_string():
    token = crypto.encrypt("", "parola")
    assert crypto.decrypt(token, "parola") == ""


def test_encrypt_decrypt_unicode_plaintext():
    plaintext = "parola öğrenmek 🔒 çok önemli"
    token = crypto.encrypt(plaintext, "parola")

    assert crypto.decrypt(token, "parola") == plaintext


@pytest.mark.parametrize("plaintext", ["", "a", "gizli mesaj: StegoCrypt 123", "öğrenmek 🔒" * 5])
def test_encrypted_length_matches_actual_encrypt_output(plaintext):
    predicted = crypto.encrypted_length(len(plaintext.encode("utf-8")))

    assert len(crypto.encrypt(plaintext, "parola")) == predicted


def test_decrypt_with_zero_length_ciphertext_raises():
    # salt(16) + iv(16) + mac(32) = 64 byte, ciphertext icin hic yer yok
    token = os.urandom(crypto.SALT_SIZE + crypto.IV_SIZE + crypto.MAC_SIZE)

    with pytest.raises(DecryptionError):
        crypto.decrypt(token, "parola")
