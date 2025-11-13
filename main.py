import base64, io, flet as ft
from PIL import Image
import qrcode
from constants import TRANSPARENT_PNG

def make_qr_png_bytes(text: str) -> bytes:
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
    
    # Title
    title = ft.Text("QR Code Generator", size=22, weight=ft.FontWeight.BOLD)
    # Input field for text to encode
    input = ft.TextField(label="Text", multiline=True, min_lines=3)
    # Button to generate QR code 
    generate_button = ft.ElevatedButton("Generate", on_click=lambda _: gen())
    # Default Image to display the QR code
    img = ft.Image(src_base64=TRANSPARENT_BASE64_PNG, width=320, height=320, fit=ft.ImageFit.CONTAIN, border_radius=8)

    def gen():
        text = input.value.strip()
        if not text:
            img.visible = False
        else:
            png = make_qr_png_bytes(text)
            img.src = None
            img.src_base64 = base64.b64encode(png).decode()
            img.visible = True
        page.update()

    page.add(ft.Column([title,
                        input,
                        generate_button,
                        img]))

if __name__ == "__main__":
    ft.app(target=main)