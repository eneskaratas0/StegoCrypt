"""AES-256-CBC + HMAC-SHA256 (Encrypt-then-MAC) sifreleme ve PBKDF2 anahtar turetme fonksiyonlari."""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, hmac, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.exceptions import DecryptionError

SALT_SIZE = 16
IV_SIZE = 16
KEY_SIZE = 32  # 256 bit (AES anahtari icin)
MAC_KEY_SIZE = 32  # HMAC-SHA256 anahtari icin
MAC_SIZE = 32  # HMAC-SHA256 ciktisi
BLOCK_SIZE = algorithms.AES.block_size // 8  # 16 byte
PBKDF2_ITERATIONS = 600_000  # OWASP 2026 PBKDF2-HMAC-SHA256 onerisi


def encrypted_length(plaintext_byte_len: int) -> int:
    """encrypt() ciktisinin, sifreleme calistirmadan, tam olarak kac bayt olacagini hesaplar.

    Cagiranlarin (orn. CLI'nin kapasite on-kontrolu) PBKDF2 anahtar turetmesini
    (600k iterasyon) calistirmadan once erken basarisiz olabilmesi icin kullanilir.
    """
    padded_len = (plaintext_byte_len // BLOCK_SIZE + 1) * BLOCK_SIZE
    return SALT_SIZE + IV_SIZE + padded_len + MAC_SIZE


def derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    """Parola ve salt'tan tek PBKDF2 cagrisiyla ayri sifreleme ve MAC anahtarlari turetir."""
    master = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE + MAC_KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    ).derive(password.encode("utf-8"))
    return master[:KEY_SIZE], master[KEY_SIZE:]


def _new_hmac(mac_key: bytes, salt: bytes, iv: bytes, ciphertext: bytes) -> hmac.HMAC:
    h = hmac.HMAC(mac_key, hashes.SHA256())
    h.update(salt + iv + ciphertext)
    return h


def encrypt(plaintext: str, password: str) -> bytes:
    """Metni AES-256-CBC ile sifreler, HMAC-SHA256 ile imzalar (Encrypt-then-MAC).

    Donen format: salt(16) + iv(16) + ciphertext + hmac(32)
    """
    salt = os.urandom(SALT_SIZE)
    iv = os.urandom(IV_SIZE)
    enc_key, mac_key = derive_keys(password, salt)

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    encryptor = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    mac = _new_hmac(mac_key, salt, iv, ciphertext).finalize()
    return salt + iv + ciphertext + mac


def decrypt(token: bytes, password: str) -> str:
    """encrypt() ile uretilmis token'i dogrular ve cozer.

    MAC once dogrulanir (verify-then-decrypt); dogrulama basarisiz olursa
    sifre cozme hic denenmez. Bu, CBC padding-oracle saldirilarini engeller.
    Yanlis parola, bozuk veri veya kurcalanmis (tampered) veride DecryptionError firlatir.
    """
    ciphertext_len = len(token) - SALT_SIZE - IV_SIZE - MAC_SIZE
    if ciphertext_len <= 0 or ciphertext_len % BLOCK_SIZE != 0:
        raise DecryptionError("Gecersiz token: veri cok kisa veya bozuk")

    salt = token[:SALT_SIZE]
    iv = token[SALT_SIZE:SALT_SIZE + IV_SIZE]
    ciphertext = token[SALT_SIZE + IV_SIZE:-MAC_SIZE]
    received_mac = token[-MAC_SIZE:]

    enc_key, mac_key = derive_keys(password, salt)

    try:
        _new_hmac(mac_key, salt, iv, ciphertext).verify(received_mac)
    except InvalidSignature as exc:
        raise DecryptionError("Sifre cozme basarisiz: yanlis parola veya bozuk/kurcalanmis veri") from exc

    try:
        decryptor = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise DecryptionError("Sifre cozme basarisiz: yanlis parola veya bozuk/kurcalanmis veri") from exc
