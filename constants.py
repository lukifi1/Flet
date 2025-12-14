import base64
from enum import Enum

import qrcode
import qrcode.constants

# Transparent 1x1 PNG image byte data
TRANSPARENT_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
# Base64 encoded transparent PNG
TRANSPARENT_BASE64_PNG = base64.b64encode(TRANSPARENT_PNG).decode()


class QRCodeDataType(Enum):
    """Enumeration of QR code data types/formats."""

    TEXT = "Text"
    URL = "URL"
    EMAIL = "Email"
    PHONE = "Phone Number"
    SMS = "SMS"
    WIFI = "WiFi"
    GEOLOCATION = "Geolocation"


# ====================================
#       Natural Language Patterns
# ====================================
# NLP patterns for auto detection

# PHONE_NUMBER_PATTERN = r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
PHONE_NUMBER_PATTERN = (
    r"\+?\d{1,4}[-.\s]?"          # optional country code with +, e.g. +1, +49, 0049 (first part)
    r"(?:\(\d{1,3}\)|\d{1,3})"    # area code: either (415) or 415, but NO dangling '('
    r"[-.\s]?\d{1,4}"             # first local part
    r"[-.\s]?\d{1,4}"             # second local part
    r"(?:[-.\s]?\d{1,9})?"        # optional extra block (for long internationals)
)
EMAIL_PATTERN = r"([^@\s]+@[^@\s]+\.[^@\s]+)(?:\?.*)?"
DOMAIN_PATTERN = r"(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s]*)?"
SMS_PATTERN = r"(\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(\?body=.*)?"
WIFI_PATTERN = r"T:(WEP|WPA|nopass);S:.*;P:.*;;"
GEOLOCATION_PATTERN = r"-?\d+(\.\d+)?,-?\d+(\.\d+)?"

# Mapping of QR code data types to their regex patterns
TYPE_PATTERNS = {
    # Natural Language Patterns
    QRCodeDataType.PHONE: PHONE_NUMBER_PATTERN,
    QRCodeDataType.EMAIL: EMAIL_PATTERN,
    QRCodeDataType.URL: DOMAIN_PATTERN,
    # Additional Patterns
    QRCodeDataType.SMS: SMS_PATTERN,
    QRCodeDataType.WIFI: WIFI_PATTERN,
    QRCodeDataType.GEOLOCATION: GEOLOCATION_PATTERN,
}

# Mapping of QR code data types to their URI schemes
URI_SCHEMES = {
    QRCodeDataType.URL: ["https://", "http://"],
    QRCodeDataType.EMAIL: "mailto:",
    QRCodeDataType.PHONE: "tel:",
    QRCodeDataType.SMS: "sms:",
    QRCodeDataType.GEOLOCATION: "geo:",
    QRCodeDataType.WIFI: "WIFI:",
}

# ====================================
#       QR Code ECC Configuration
# ====================================


class QRCodeEccLevel(Enum):
    """Enumeration of QR code error correction levels."""

    L = "L"  # Low
    M = "M"  # Medium
    Q = "Q"  # Quartile
    H = "H"  # High
    NA = "N/A"  # Not Applicable


# QR Code capacity limits for version 40 and error correction levels
QR_LIMITS = {
    QRCodeEccLevel.L: 2953,  # Low error correction
    QRCodeEccLevel.M: 2331,  # Medium error correction
    QRCodeEccLevel.Q: 1663,  # Quartile error correction
    QRCodeEccLevel.H: 1273,  # Highest error correction
}
# Colors associated with each ECC level
QR_ECC_LEVEL_COLORS = {
    QRCodeEccLevel.L: "#dc3545",  # Red
    QRCodeEccLevel.M: "#fd7e14",  # Orange
    QRCodeEccLevel.Q: "#0d6efd",  # Blue
    QRCodeEccLevel.H: "#26C77C",  # Green
    QRCodeEccLevel.NA: "#6c757d",  # Grey
}
# Descriptive messages for each ECC level
QR_ECC_LEVEL_MESSAGES = {
    QRCodeEccLevel.L: "Low ECC (7%)",
    QRCodeEccLevel.M: "Medium ECC (15%)",
    QRCodeEccLevel.Q: "Quartile ECC (25%)",
    QRCodeEccLevel.H: "High ECC (30%)",
    QRCodeEccLevel.NA: "N/A",
}
# Error correction capability messages for each ECC level
QR_ECC_LEVEL_ERROR_MESSAGES = {
    QRCodeEccLevel.L: "Minimal error correction, suitable for clean environments.",
    QRCodeEccLevel.M: "Balanced error correction for general use.",
    QRCodeEccLevel.Q: "Higher error correction for challenging conditions.",
    QRCodeEccLevel.H: "Maximum error correction for harsh environments.",
    QRCodeEccLevel.NA: "Too large for any QR code! ❌",
}

# Mapping of QR code ECC levels to qrcode library constants
ECC_FUNCTION_MAP = {
    QRCodeEccLevel.L: qrcode.constants.ERROR_CORRECT_L,
    QRCodeEccLevel.M: qrcode.constants.ERROR_CORRECT_M,
    QRCodeEccLevel.Q: qrcode.constants.ERROR_CORRECT_Q,
    QRCodeEccLevel.H: qrcode.constants.ERROR_CORRECT_H,
}
# Order of ECC levels from highest to lowest
ECC_ORDER = [
    QRCodeEccLevel.H,
    QRCodeEccLevel.Q,
    QRCodeEccLevel.M,
    QRCodeEccLevel.L,
]

# ====================================
#       QR Code Configuration
# ====================================
QR_FILL_COLOR = "black"
QR_BACK_COLOR = "white"
QR_NO_DATA_IMAGE = "/no-qrcode.png"  # Path to "no data" image asset

# ====================================
#       Logo Configuration
# ====================================

# Path to logo image asset
LOGO_PATH = "assets/logo-color.png"
# Logo area as a ratio of QR code size in percentage
LOGO_AREA_RATIO = 0.22
# Logo padding as a ratio of logo size
LOGO_AREA_PADDING_RATIO = 0
# Logo corner radius as a ratio of logo size
LOGO_AREA_RADIUS_RATIO = 0.25
# Minimum ECC level required when adding a logo
LOGO_MIN_ECC_LEVEL = QRCodeEccLevel.H
