import base64, io, flet as ft
from PIL import Image
import qrcode

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
    inp = ft.TextField(label="Text", multiline=True, min_lines=3, on_change=lambda e: gen())
    img = ft.Image(width=320, height=320, fit=ft.ImageFit.CONTAIN, border_radius=8)

    def gen():
        png = make_qr_png_bytes(inp.value.strip())
        img.src = "data:image/png;base64," + base64.b64encode(png).decode()
        page.update()

    page.add(ft.Column([ft.Text("QR Code Generator", size=22, weight=ft.FontWeight.BOLD),
                        inp,
                        ft.ElevatedButton("Generate", on_click=lambda _: gen()),
                        img]))
    gen()

if __name__ == "__main__":
    ft.app(target=main)