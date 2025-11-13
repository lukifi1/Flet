import base64
from enum import Enum

# Transparent 1x1 PNG image byte data
TRANSPARENT_PNG=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82'
# Base64 encoded transparent PNG
TRANSPARENT_BASE64_PNG=base64.b64encode(TRANSPARENT_PNG).decode()

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

PHONE_NUMBER_PATTERN = r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}"
EMAIL_PATTERN = r"([^@\s]+@[^@\s]+\.[^@\s]+)(?:\?.*)?"
DOMAIN_PATTERN = r"(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s]*)?"
SMS_PATTERN = r"(\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(\?body=.*)?"
WIFI_PATTERN = r"T:(WEP|WPA|nopass);S:.*;P:.*;;"
GEOLOCATION_PATTERN = r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?"

# Mapping of QR code data types to their regex patterns
TYPE_PATTERNS = {
    # Natural Language Patterns
    QRCodeDataType.PHONE : PHONE_NUMBER_PATTERN,
    QRCodeDataType.EMAIL : EMAIL_PATTERN,
    QRCodeDataType.URL : DOMAIN_PATTERN,
    # Additional Patterns
    QRCodeDataType.SMS : SMS_PATTERN,
    QRCodeDataType.WIFI : WIFI_PATTERN,
    QRCodeDataType.GEOLOCATION : GEOLOCATION_PATTERN,
}

# Mapping of QR code data types to their URI schemes
URI_SCHEMES = {
    QRCodeDataType.URL : ["https://", "http://"],
    QRCodeDataType.EMAIL : "mailto:",
    QRCodeDataType.PHONE : "tel:",
    QRCodeDataType.SMS : "sms:",
    QRCodeDataType.GEOLOCATION : "geo:",
    QRCodeDataType.WIFI : "WIFI:",
}