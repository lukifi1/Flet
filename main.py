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
    inp = ft.TextField(label="Text", multiline=True, min_lines=3)
    transparent_png = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82').decode()
    img = ft.Image(src_base64=transparent_png, width=320, height=320, fit=ft.ImageFit.CONTAIN, border_radius=8)

    def gen():
        text = inp.value.strip()
        if not text:
            img.visible = False
        else:
            png = make_qr_png_bytes(text)
            img.src = None
            img.src_base64 = base64.b64encode(png).decode()
            img.visible = True
        page.update()

    page.add(ft.Column([ft.Text("QR Code Generator", size=22, weight=ft.FontWeight.BOLD),
                        inp,
                        ft.ElevatedButton("Generate", on_click=lambda _: gen()),
                        img]))

if __name__ == "__main__":
    ft.app(target=main)