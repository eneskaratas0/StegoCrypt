import pytest

from core import stego


def test_encode_not_implemented():
    with pytest.raises(NotImplementedError):
        stego.encode("in.png", b"data", "out.png")
