import pytest

from core import crypto


def test_encrypt_not_implemented():
    with pytest.raises(NotImplementedError):
        crypto.encrypt(b"data", "password")
