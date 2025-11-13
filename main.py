import base64, io, flet as ft
from PIL import Image
import qrcode
from constants import QRCodeDataType, TRANSPARENT_BASE64_PNG
from utils import get_qrcode_type, prepend_uri_scheme

def make_qr_png_bytes(text: str) -> bytes:
    # TODO: logging
    print(f"Generating QR code for text: {text}")
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q)
    qr.add_data(text or "")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def main(page: ft.Page):
    page.title = "QR Maker"
    page.padding = 16
 
    # QR Code Data Type Badge
    badge_type = ft.Text(QRCodeDataType.TEXT.value, color="white", size=12)
    badge = ft.Container(
        content=badge_type,
        bgcolor="#0d6efd",
        padding=ft.padding.symmetric(vertical=4, horizontal=8),
        border_radius=12,
    )
    format_display = ft.Row([ft.Text("Format: "), badge])

    # Title
    title = ft.Text("QR Code Generator", size=22, weight=ft.FontWeight.BOLD)
    # Input field for text to encode
    input = ft.TextField(label="Text", multiline=True, min_lines=3, on_change=lambda e: handle_input_change(e), expand=False)
    # Button to generate QR code 
    generate_button = ft.ElevatedButton("Generate", on_click=lambda _: gen())
    # Default Image to display the QR code
    img = ft.Image(src_base64=TRANSPARENT_BASE64_PNG, width=320, height=320, fit=ft.ImageFit.CONTAIN, border_radius=8)

    def handle_input_change(e):
        qrcode_type = get_qrcode_type(e.control.value)
        badge_type.value = qrcode_type.value
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
            png = make_qr_png_bytes(text)
            img.src = None
            img.src_base64 = base64.b64encode(png).decode()
            img.visible = True
        page.update()

    page.add(ft.Column([title,
                        input,
                        format_display,
                        generate_button,
                        img]))

if __name__ == "__main__":
    ft.app(target=main)