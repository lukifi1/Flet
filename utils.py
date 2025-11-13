from constants import QRCodeDataType, QRCodeEccLevel, TYPE_PATTERNS, URI_SCHEMES, QR_LIMITS, ECC_FUNCTION_MAP, ECC_ORDER, QR_ECC_LEVEL_COLORS, QR_ECC_LEVEL_MESSAGES, QR_ECC_LEVEL_ERROR_MESSAGES
import re

def get_qrcode_type(text: str) -> QRCodeDataType:
    """Determine the QR code data type based on the input text."""
    # Check against each pattern
    for data_type, pattern in TYPE_PATTERNS.items():
        # Get the corresponding URI
        scheme = URI_SCHEMES.get(data_type)
        scheme_list = [scheme] if isinstance(scheme, str) else scheme 
            
        curr_pattern = pattern
        for scheme in scheme_list or [None]:
            # allow the URI scheme to be optional (case-insensitive) before the pattern
            if scheme:
                curr_pattern = r"(?i:" + re.escape(scheme) + r")?" + pattern
                
            # Allow leading/trailing whitespace
            curr_pattern = r"^\s*" + curr_pattern + r"\s*$"  

            # print(f"Checking type {data_type} with pattern: {curr_pattern}")

            # Compile the regex pattern
            regex_pattern = re.compile(curr_pattern)

            if re.fullmatch(regex_pattern, text.strip()):
                print(f"Matched type: {data_type}")
                return data_type


    # If no patterns match, return TEXT as default
    return QRCodeDataType.TEXT


def prepend_uri_scheme(text: str, data_type: QRCodeDataType) -> str:
    """Prepend the appropriate URI scheme to the text if necessary."""
    print (f"Prepending URI scheme for data type: {data_type} and text: {text}")

    # If the data type has no associated URI scheme, return the text as is
    if data_type not in URI_SCHEMES:
        return text
    
    # Get the list of schemes for the data type
    schemes = URI_SCHEMES.get(data_type)
    if isinstance(schemes, str):
        schemes = [schemes]

    # Check if the text already starts with any of the schemes
    for scheme in schemes:
        # Escape for safe regex
        if re.match(rf"^{re.escape(scheme)}", text, re.IGNORECASE):
            # print(f"Text already starts with scheme {scheme}.")
            return text
        
    # Prepend the default scheme (first in the list)
    default_scheme = schemes[0] if schemes else ""
    # print(f"Prepending using default scheme {default_scheme}.")
    return default_scheme + text

def qrcode_select_best_ecc(data: str):
    length = len(data.encode("utf-8"))
    for ecc in ECC_ORDER:
        if length <= QR_LIMITS[ecc]:
            return ECC_FUNCTION_MAP[ecc] 
    
    return None  # too large for any QR code

def qrcode_get_ecc_level(data: str) -> QRCodeEccLevel:
    length = len(data.encode("utf-8"))
    # Select the lowest ECC level that can accommodate the data length
    for ecc in ECC_ORDER:
        if length <= QR_LIMITS[ecc]:
            return ecc
    
    return QRCodeEccLevel.NA # too large for any QR code

def qrcode_get_data_info(data: str) -> dict:
    """Get information about the QR code data."""
    length = len(data.encode("utf-8"))
    ecc_level = qrcode_get_ecc_level(data)
    return f"{length} bytes - " + QR_ECC_LEVEL_MESSAGES.get(ecc_level, "") + " - " + QR_ECC_LEVEL_ERROR_MESSAGES.get(ecc_level, "")