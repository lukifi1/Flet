import asyncio
import mimetypes

import cv2
import flet as ft
import flet_camera as fc
import flet_permission_handler as fph
import numpy as np

from app.core.constants import (
    UI_ACCENT,
    UI_BUTTON_RADIUS,
    UI_INPUT_BG,
    UI_PAGE_BG,
    UI_TEXT_DARK,
    UI_TEXT_LIGHT,
    UI_TEXT_MUTED,
)
from app.core.transfer.chunker import IntegrityError, Reassembler
from app.core.transfer.payload import PayloadError


def _get_receiver(page: ft.Page) -> Reassembler:
    receiver = getattr(page, "transfer_receiver", None)
    if receiver is None:
        receiver = Reassembler()
        page.transfer_receiver = receiver
    if not hasattr(page, "transfer_verified"):
        page.transfer_verified = False
    if not hasattr(page, "receive_status"):
        page.receive_status = None
    return receiver


def _decode_qr(encoded_image: bytes, detector: cv2.QRCodeDetector) -> str | None:
    image = cv2.imdecode(np.frombuffer(encoded_image, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return None

    # The guide rectangle covers the center of the camera preview. Searching
    # only that square reduces the work and discourages poorly framed scans.
    height, width = image.shape[:2]
    side = int(min(height, width) * 0.72)
    left = (width - side) // 2
    top = (height - side) // 2
    center = image[top:top + side, left:left + side]
    return detector.detectAndDecode(center)[0] or None


def receive_view(page: ft.Page) -> ft.View:
    receiver = _get_receiver(page)
    progress = ft.ProgressBar(value=0, width=420, color=UI_ACCENT)
    count = ft.Text("0 Pakete empfangen", color=UI_TEXT_DARK)
    status = ft.Text(
        getattr(page, "receive_status", None)
        or "Starte den Live-Scan und richte den QR-Code im Rahmen aus.",
        color=UI_TEXT_MUTED,
    )
    missing = ft.Text("", selectable=True, size=12, color=UI_TEXT_MUTED)
    save_button = ft.Button(
        "Datei speichern",
        height=44,
        color=UI_TEXT_MUTED,
        bgcolor=UI_INPUT_BG,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        disabled=True,
    )
    open_button = ft.Button(
        "In anderer App öffnen",
        height=44,
        color=UI_TEXT_LIGHT,
        bgcolor=UI_ACCENT,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        disabled=True,
    )
    picker = ft.FilePicker()
    page.services.append(picker)
    share = ft.Share()

    def refresh_progress():
        total = receiver.total or 0
        count.value = f"{receiver.received}/{total} Pakete empfangen" if total else f"{receiver.received} Pakete empfangen"
        progress.value = receiver.received / total if total else 0
        absent = receiver.missing()
        if absent:
            sample = ", ".join(str(i) for i in absent[:30])
            suffix = " …" if len(absent) > 30 else ""
            missing.value = f"Fehlende Chunk-Nummern (0-basiert): {sample}{suffix}"
        else:
            missing.value = ""
        save_button.disabled = not page.transfer_verified
        open_button.disabled = not page.transfer_verified

    async def start_scan(_):
        await page.push_route("/receive/scan")

    async def save_file(_):
        if not receiver.is_complete:
            return
        try:
            data = receiver.assemble()
            filename = receiver.meta.filename.replace("\\", "/").split("/")[-1] or "empfangene-datei.bin"
            target = await picker.save_file(
                dialog_title="Empfangene Datei speichern",
                file_name=filename,
                src_bytes=data,
            )
            if target:
                status.value = f"Datei gespeichert: {target}"
            page.update()
        except (IntegrityError, OSError) as exc:
            status.value = f"Speichern fehlgeschlagen: {exc}"
            page.update()

    async def open_in_app(_):
        if not receiver.is_complete or not page.transfer_verified:
            return
        try:
            data = receiver.assemble()
            filename = receiver.meta.filename.replace("\\", "/").split("/")[-1] or "empfangene-datei.bin"
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            shared_file = ft.ShareFile.from_bytes(
                data,
                mime_type=mime_type,
                name=filename,
            )
            await share.share_files(
                [shared_file],
                title="Datei öffnen mit",
                text="Wähle eine App zum Öffnen der empfangenen Datei.",
            )
            status.value = "Wähle im Android-Menü Notizen oder eine andere passende App."
        except Exception as exc:
            status.value = f"Öffnen fehlgeschlagen: {exc}"
        page.update()

    def reset(_):
        nonlocal receiver
        receiver = Reassembler()
        page.transfer_receiver = receiver
        page.transfer_verified = False
        page.receive_status = None
        start_button.disabled = False
        refresh_progress()
        status.value = "Empfang zurückgesetzt."
        page.update()

    start_button = ft.Button(
        "Live-Scan starten",
        height=44,
        color=UI_TEXT_LIGHT,
        bgcolor=UI_ACCENT,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        on_click=start_scan,
    )
    start_button.disabled = page.transfer_verified
    save_button.on_click = save_file
    open_button.on_click = open_in_app

    refresh_progress()
    return ft.View(
        route="/receive",
        bgcolor=UI_PAGE_BG,
        controls=[
            ft.SafeArea(
                ft.Container(
                    expand=True,
                    padding=24,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        [
                            ft.Text("Datei empfangen", size=24, weight=ft.FontWeight.W_700, color=UI_TEXT_DARK),
                            ft.Text("FLT1 QR-Sequenz scannen und Datei zusammensetzen", size=14, color=UI_TEXT_MUTED),
                            start_button,
                            progress,
                            count,
                            status,
                            missing,
                            open_button,
                            ft.Text(
                                "Öffnet die Android-App-Auswahl; Speichern ist optional.",
                                size=12,
                                color=UI_TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            save_button,
                            ft.TextButton("Empfang zurücksetzen", on_click=reset),
                            ft.Text("Technisches Limit: 50 MiB.", size=12, color=UI_TEXT_MUTED),
                        ],
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                expand=True,
            )
        ],
    )


def scan_view(page: ft.Page) -> ft.View:
    receiver = _get_receiver(page)
    camera_running = False
    camera_initialized = False

    # Let the native camera preview keep its own aspect ratio. The camera still
    # fills the fullscreen SafeArea; the scan controls remain a separate overlay.
    camera = fc.Camera(expand=True, preview_enabled=True)
    qr_detector = cv2.QRCodeDetector()
    permission_handler = fph.PermissionHandler()
    page.services.append(permission_handler)

    status = ft.Text("Kamerazugriff wird angefragt …", color=ft.Colors.WHITE, size=13)
    count = ft.Text("0 Pakete", color=ft.Colors.WHITE, size=15, weight=ft.FontWeight.W_600)
    progress = ft.ProgressBar(value=0, width=150, color=UI_ACCENT, bgcolor="#66FFFFFF")

    async def focus_qr(_e=None):
        if not camera_initialized:
            status.value = "Kamera wird noch gestartet"
            page.update()
            return
        try:
            await camera.set_focus_mode(fc.FocusMode.AUTO)
            await camera.set_focus_point(ft.Offset(0.5, 0.5))
            status.value = "Autofokus auf den QR-Code ausgelöst"
        except Exception:
            status.value = "Fokussieren wird von dieser Kamera nicht unterstützt"
        page.update()

    def update_progress():
        total = receiver.total or 0
        count.value = f"{receiver.received}/{total} Pakete" if total else f"{receiver.received} Pakete"
        progress.value = receiver.received / total if total else 0

    def accept(text: str):
        try:
            if receiver.add(text):
                update_progress()
                if receiver.is_complete:
                    receiver.assemble()
                    status.value = f"{receiver.meta.filename} empfangen · SHA-256 geprüft"
                    page.transfer_verified = True
                    page.receive_status = "Alle Pakete empfangen. SHA-256 stimmt; Kamera wurde beendet."
                else:
                    status.value = "Paket erkannt · Sender-Loop weiterlaufen lassen"
                page.update()
        except (PayloadError, IntegrityError) as exc:
            status.value = f"Scanfehler: {exc}"
            page.update()

    async def scan_loop():
        nonlocal camera_running
        nonlocal camera_initialized
        try:
            permission = await permission_handler.request(fph.Permission.CAMERA)
            if permission != fph.PermissionStatus.GRANTED:
                status.value = "Kamerazugriff nicht erlaubt. Bitte Geräte- oder Browserberechtigung prüfen."
                page.update()
                return

            if not camera_initialized:
                cameras = await camera.get_available_cameras()
                if not cameras:
                    raise RuntimeError("Auf diesem Gerät wurde keine Kamera gefunden.")
                selected_camera = next(
                    (item for item in cameras if item.lens_direction == fc.CameraLensDirection.BACK),
                    cameras[0],
                )
                await camera.initialize(
                    description=selected_camera,
                    resolution_preset=fc.ResolutionPreset.MEDIUM,
                    enable_audio=False,
                    image_format_group=fc.ImageFormatGroup.JPEG,
                )
                try:
                    await camera.set_focus_mode(fc.FocusMode.AUTO)
                    await camera.set_focus_point(ft.Offset(0.5, 0.5))
                except Exception:
                    pass
                camera_initialized = True

            camera_running = True
            status.value = "QR-Code ruhig im Hilfsrahmen halten"
            page.update()

            # Keep the camera preview local and smooth. Only request occasional
            # still frames for decoding instead of streaming every frame over Wi-Fi.
            while camera_running:
                image_bytes = await camera.take_picture()
                text = await asyncio.to_thread(_decode_qr, image_bytes, qr_detector)
                if text:
                    accept(text)
                if page.transfer_verified:
                    camera_running = False
                    try:
                        await camera.pause_preview()
                    except Exception:
                        pass
                    await page.push_route("/receive")
                    return
                await asyncio.sleep(0.05)
        except Exception as exc:
            status.value = f"Kamerafehler: {exc}"
            page.update()
        finally:
            camera_running = False

    async def finish_scan(_):
        nonlocal camera_running
        camera_running = False
        if camera_initialized:
            try:
                await camera.pause_preview()
            except Exception:
                pass
        await page.push_route("/receive")

    guide = ft.GestureDetector(
        on_tap=focus_qr,
        content=ft.Container(
            width=270,
            height=270,
            border=ft.Border.all(3, ft.Colors.WHITE),
            border_radius=16,
        ),
    )
    overlay = ft.Stack(
        expand=True,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=guide,
            ),
            ft.Container(
                left=12,
                top=12,
                bgcolor="#AA000000",
                border_radius=24,
                content=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Zurück",
                    on_click=finish_scan,
                ),
            ),
            ft.Container(
                left=64,
                top=18,
                right=12,
                content=ft.Text("QR-Code ausrichten · Rahmen antippen zum Fokussieren", color=ft.Colors.WHITE, size=13),
            ),
            ft.Container(
                right=12,
                bottom=18,
                bgcolor="#CC000000",
                padding=12,
                border_radius=12,
                content=ft.Column(
                    [count, progress, status],
                    tight=True,
                    spacing=6,
                ),
            ),
        ],
    )

    view = ft.View(
        route="/receive/scan",
        padding=0,
        bgcolor=ft.Colors.BLACK,
        controls=[
            ft.SafeArea(
                expand=True,
                content=ft.Stack(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    controls=[camera, overlay],
                ),
            )
        ],
    )
    page.run_task(scan_loop)
    return view
