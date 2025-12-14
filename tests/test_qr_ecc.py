import pytest
from utils import qrcode_select_best_ecc


def test_short_text_uses_low_ecc():
    ecc = qrcode_select_best_ecc("Hello")
    assert ecc is not None
    assert ecc != "H"  # Should select lower ECC


def test_long_text_still_selects_ecc():
    text = "A" * 500
    ecc = qrcode_select_best_ecc(text)
    assert ecc is not None


def test_too_long_text_returns_none():
    text = "A" * 5000
    ecc = qrcode_select_best_ecc(text)
    assert ecc is None
