import asyncio
import base64
import io

import flet as ft
import qrcode
import qrcode.constants

from app.core.constants import TRANSPARENT_BASE64_PNG
from app.core.transfer.chunker import DEFAULT_CHUNK_SIZE, build_frames

DEFAULT_TEXT = "Default Text test .... " * 40


def make_qr_image(frame):
    """Frame string -> QR code as Base64 PNG, so ft.Image can show it."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
    qr.add_data(frame)
    qr.make(fit=True)
    buffer = io.BytesIO()
    qr.make_image().save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def main(page: ft.Page):
    page.title = "QR Sequence Player (prototype)"
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    playing = False

    qr_image = ft.Image(src=TRANSPARENT_BASE64_PNG, width=320, height=320, fit=ft.BoxFit.CONTAIN)
    status = ft.Text("Press Start")
    text_input = ft.TextField(label="Text to send", value=DEFAULT_TEXT,
                              multiline=True, min_lines=3, max_lines=5)
    fps_slider = ft.Slider(min=1, max=15, divisions=14, value=5, label="{value} fps")
    chunk_slider = ft.Slider(min=100, max=800, divisions=7, value=DEFAULT_CHUNK_SIZE,
                             label="{value} bytes")

    async def start(e):
        nonlocal playing
        if playing:
            return

        frames = build_frames(text_input.value.encode("utf-8"), "demo.txt",
                              chunk_size=int(chunk_slider.value))
        images = [make_qr_image(f) for f in frames]

        playing = True
        i = 0
        while playing:  # loops until Stop is pressed
            index = i % len(images)
            qr_image.src = images[index]
            status.value = f"QR {index + 1}/{len(images)}"
            page.update()
            i += 1
            await asyncio.sleep(1 / fps_slider.value)

        status.value = "Stopped"
        page.update()

    def stop(e):
        nonlocal playing
        playing = False

    page.add(ft.Column([
        text_input,
        ft.Text("Speed (frames per second)"),
        fps_slider,
        ft.Text("Chunk size (bytes per QR code)"),
        chunk_slider,
        ft.Row([ft.Button("Start", on_click=start), ft.Button("Stop", on_click=stop)]),
        qr_image,
        status,
    ], spacing=10))


ft.run(main)