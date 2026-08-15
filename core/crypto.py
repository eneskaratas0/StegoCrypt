"""AES-256 sifreleme ve anahtar turetme fonksiyonlari."""

from __future__ import annotations


def derive_key(password: str, salt: bytes) -> bytes:
    """Parola ve salt'tan PBKDF2 ile 256-bit AES anahtari turetir."""
    raise NotImplementedError


def encrypt(data: bytes, password: str) -> bytes:
    """Veriyi AES-256 (GCM) ile sifreler; salt + nonce + tag + ciphertext dondurur."""
    raise NotImplementedError


def decrypt(token: bytes, password: str) -> bytes:
    """encrypt() ile uretilmis veriyi cozer. Yanlis parolada DecryptionError firlatir."""
    raise NotImplementedError
