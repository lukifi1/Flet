import asyncio
import base64
import io

import qrcode
import qrcode.constants

from app.core.logger import get_logger
from app.core.transfer.chunker import DEFAULT_CHUNK_SIZE, build_frames

log = get_logger(__name__)

FPS = 5  # QR codes per second


def make_qr_image(frame):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
    qr.add_data(frame)
    qr.make(fit=True)
    buffer = io.BytesIO()
    qr.make_image().save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


class SequencePlayer:

    def __init__(self, img, status=None):
        self.img = img
        self.status = status
        self.playing = False
        self.old_src = None
        self.text = ""
        self.first_image = None
        self.run_id = 0  # makes sure an old loop never keeps running next to a new one

    def _show_status(self, message):
        if self.status is not None:
            self.status.value = message
            self.status.update()

    async def play(self, text):
        if self.playing:
            return
        if not text:
            self._show_status("Enter some text first")
            return

        frames = build_frames(text.encode("utf-8"), "text.txt", DEFAULT_CHUNK_SIZE)
        images = [make_qr_image(frame) for frame in frames]

        self.text = text
        self.first_image = images[0]
        self.old_src = self.img.src
        self.run_id += 1
        run_id = self.run_id
        self.playing = True

        i = 0
        while self.playing and self.run_id == run_id:
            index = i % len(images)
            self.img.src = images[index]
            try:
                self.img.update()
                self._show_status(f"QR {index + 1}/{len(images)}")
            except Exception as error:  # e.g. the user left the page
                log.info("Sequence stopped: %s", error)
                if self.run_id == run_id:
                    self.playing = False
                return
            i += 1
            await asyncio.sleep(1 / FPS)

        if self.run_id == run_id:
            self._show_status("")

    def stop(self, restore=False):
        was_playing = self.playing
        self.playing = False
        if restore and was_playing:
            self.img.src = self.old_src
            self.img.update()