import sys, os, json

import pytest
from utils import get_qrcode_type
from constants import QRCodeDataType

# Load JSON test data
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "qrcode_pattern_tests.json")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)


# --------------------------
#  EMAIL TESTS
# --------------------------

@pytest.mark.parametrize("value", DATA["email_valid"])
def test_email_detection_valid(value):
    assert get_qrcode_type(value) == QRCodeDataType.EMAIL


@pytest.mark.parametrize("value", DATA["email_invalid"])
def test_email_detection_invalid(value):
    assert get_qrcode_type(value) != QRCodeDataType.EMAIL


# --------------------------
#  PHONE TESTS
# --------------------------

@pytest.mark.parametrize("value", DATA["phone_valid"])
def test_phone_detection_valid(value):
    assert get_qrcode_type(value) == QRCodeDataType.PHONE


@pytest.mark.parametrize("value", DATA["phone_invalid"])
def test_phone_detection_invalid(value):
    assert get_qrcode_type(value) != QRCodeDataType.PHONE


# --------------------------
#  URL TESTS
# --------------------------

@pytest.mark.parametrize("value", DATA["url_valid"])
def test_url_detection_valid(value):
    assert get_qrcode_type(value) == QRCodeDataType.URL


@pytest.mark.parametrize("value", DATA["url_invalid"])
def test_url_detection_invalid(value):
    assert get_qrcode_type(value) != QRCodeDataType.URL


# --------------------------
#  GEO TESTS
# --------------------------

@pytest.mark.parametrize("value", DATA["geo_valid"])
def test_geo_detection_valid(value):
    assert get_qrcode_type(value) == QRCodeDataType.GEOLOCATION


@pytest.mark.parametrize("value", DATA["geo_invalid"])
def test_geo_detection_invalid(value):
    assert get_qrcode_type(value) != QRCodeDataType.GEOLOCATION


# --------------------------
#  SMS TESTS
# --------------------------

@pytest.mark.parametrize("value", DATA["sms_valid"])
def test_sms_detection_valid(value):
    assert get_qrcode_type(value) == QRCodeDataType.SMS


@pytest.mark.parametrize("value", DATA["sms_invalid"])
def test_sms_detection_invalid(value):
    assert get_qrcode_type(value) != QRCodeDataType.SMS


# --------------------------
#  WIFI TESTS
# --------------------------

@pytest.mark.parametrize("value", DATA["wifi_valid"])
def test_wifi_detection_valid(value):
    assert get_qrcode_type(value) == QRCodeDataType.WIFI


@pytest.mark.parametrize("value", DATA["wifi_invalid"])
def test_wifi_detection_invalid(value):
    assert get_qrcode_type(value) != QRCodeDataType.WIFI


# --------------------------
#  TEXT FALLBACK TESTS
# --------------------------

@pytest.mark.parametrize("value", DATA["text_fallback"])
def test_text_detection(value):
    assert get_qrcode_type(value) == QRCodeDataType.TEXT
