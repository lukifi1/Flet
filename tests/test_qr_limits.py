from constants import QR_LIMITS
from utils import qrcode_get_ecc_level


def test_qr_limit_per_ecc_level():
    for ecc_level, limit in QR_LIMITS.items():
        text = "A" * limit
        assert len(text.encode("utf-8")) <= limit


def test_qr_exceed_limit():
    ecc_level = qrcode_get_ecc_level("A" * 10)
    limit = QR_LIMITS[ecc_level]
    text = "A" * (limit + 1)

    assert len(text.encode("utf-8")) > limit
