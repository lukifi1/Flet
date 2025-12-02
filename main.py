import base64, io, flet as ft
from PIL import Image, ImageDraw
import qrcode
from constants import QRCodeDataType, TRANSPARENT_BASE64_PNG, QR_LIMITS, QR_ECC_LEVEL_COLORS, QR_ECC_LEVEL_ERROR_MESSAGES, QR_ECC_LEVEL_MESSAGES, LOGO_PATH, LOGO_AREA_RATIO, LOGO_AREA_PADDING_RATIO, LOGO_AREA_RADIUS_RATIO, ECC_FUNCTION_MAP, LOGO_MIN_ECC_LEVEL
from utils import get_qrcode_type, prepend_uri_scheme, qrcode_select_best_ecc, qrcode_get_ecc_level, qrcode_get_data_info

 
def add_logo_inside_qr(qr_img: Image.Image, logo_path: str) -> Image.Image:
    """
    Add a logo image inside the center of the QR code image, with a dedicated room/area.
    Args:
        qr_img (Image.Image): The QR code image.
        logo_path (str): The file path to the logo image.
    """
    qr_img = qr_img.convert("RGBA")

    logo = Image.open(logo_path).convert("RGBA")

    qr_w, qr_h = qr_img.size

    # Logo area = 22% of QR size (safe)
    logo_size = int(qr_w * LOGO_AREA_RATIO)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    x = (qr_w - logo_size) // 2
    y = (qr_h - logo_size) // 2

    # 1. CUT OUT AREA IN QR (true blank space)
    mask = Image.new("RGBA", qr_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)

    padding = int(logo_size * LOGO_AREA_PADDING_RATIO)
    radius = int(logo_size * LOGO_AREA_RADIUS_RATIO)

    # Draw rounded rectangle (cut-out area)
    draw.rounded_rectangle(
        (x - padding, y - padding, x + logo_size + padding, y + logo_size + padding),
        radius=radius,
        fill=(255, 255, 255, 255)
    )

    qr_img = Image.alpha_composite(qr_img, mask)

    # 2. PASTE LOGO INTO THE CUT-OUT AREA
    qr_img.paste(logo, (x, y), logo)

    return qr_img
 
def make_qr_png_bytes(text: str, logo_path: str | None = None) -> bytes:
    # TODO: logging
    print(f"Generating QR code for text: {text}")

    ecc = qrcode_select_best_ecc(text)

    if ecc is None:
        raise ValueError("Input text is too long to encode in a QR code.")
    
    qr = qrcode.QRCode(error_correction=ecc)
    qr.add_data(text or "")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Add logo if provided and the ECC level is High
    if logo_path and ecc == ECC_FUNCTION_MAP[LOGO_MIN_ECC_LEVEL]:
        img = add_logo_inside_qr(img, logo_path)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def main(page: ft.Page):
    page.title = "QR Maker"
    page.scroll = "auto"
    page.padding = 16
    
    # ============= Title ================
    title = ft.Text("QR Code Generator", size=22, weight=ft.FontWeight.BOLD)

    # ============= Format Badge ================
    # QR Code Data Type Badge
    badge_type = ft.Text(QRCodeDataType.TEXT.value, color="white", size=12)
    badge = ft.Container(
        content=badge_type,
        bgcolor="#0d6efd",
        padding=ft.padding.symmetric(vertical=4, horizontal=8),
        border_radius=12,
    )
    format_display = ft.Row([ft.Text("Format: "), badge])

    # ============= ECC Badge ================
    ecc_type = ft.Text("H", color="white", size=12)
    ecc_badge = ft.Container(
        content=ecc_type,
        bgcolor=QR_ECC_LEVEL_COLORS[qrcode_get_ecc_level("")],
        padding=ft.padding.symmetric(vertical=4, horizontal=8),
        border_radius=12,
    )
    ecc_display = ft.Row([ft.Text("ECC: "), ecc_badge])

    # ============= Input Field for QRCode ================
    input = ft.TextField(
        label="Text", 
        multiline=True, 
        min_lines=5, 
        max_lines=None, 
        height=150, 
        on_change=lambda 
        e: handle_input_change(e), 
    )

    # Button to generate QR code 
    generate_button = ft.ElevatedButton("Generate", on_click=lambda _: gen())
    # Default Image to display the QR code
    img = ft.Image(src_base64=TRANSPARENT_BASE64_PNG, width=320, height=320, fit=ft.ImageFit.CONTAIN, border_radius=8)
    # Character info display
    char_info = ft.Text("", size=12)

    def handle_input_change(e):
        text = e.control.value or ""
        raw = e.control.value or ""
        length_bytes = len(raw.encode("utf-8"))

        qrcode_type = get_qrcode_type(text)
        badge_type.value = qrcode_type.value

        ecc_level = qrcode_get_ecc_level(text)
        ecc_type.value = ecc_level.value
        ecc_badge.bgcolor = QR_ECC_LEVEL_COLORS[ecc_level]
        char_info.value = qrcode_get_data_info(text)
        char_info.color = QR_ECC_LEVEL_COLORS[ecc_level]
        generate_button.disabled = length_bytes > QR_LIMITS.get(ecc_level, 0)
        page.update()

    def gen():
        text = input.value.strip()
        if not text:
            img.visible = False
        else:
            qrcode_type = get_qrcode_type(text)
            # Prepend URI scheme if necessary
            text = prepend_uri_scheme(text, qrcode_type) 
            # Generate QR code PNG bytes
            png = make_qr_png_bytes(text, logo_path=LOGO_PATH)
            img.src = None
            img.src_base64 = base64.b64encode(png).decode()
            img.visible = True
        page.update()

    page.add(ft.Column([title,
                        input,
                        char_info,
                        format_display,
                        ecc_display,
                        generate_button,
                        img]))

if __name__ == "__main__":
    ft.app(target=main)