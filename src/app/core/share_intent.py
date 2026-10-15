"""Filesystem bridge for Android ACTION_SEND payloads."""

from __future__ import annotations

import json
import base64
import tempfile
from pathlib import Path
from typing import Any, Iterator


def android_files_dirs(package: str = "com.flet.my_app") -> list[Path]:
    """Return plausible Android app files directories, most likely first."""
    candidates = [
        Path.cwd(),
        Path.home(),
        Path(tempfile.gettempdir()).parent / "files",
        Path(f"/data/user/0/{package}/files"),
        Path(f"/data/data/{package}/files"),
    ]
    result: list[Path] = []
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate not in result:
            result.append(candidate)
    return result


def consume_payloads(package: str = "com.flet.my_app") -> Iterator[dict[str, Any]]:
    """Yield complete payloads and remove their queue files after parsing."""
    for files_dir in android_files_dirs(package):
        inbox = files_dir / "share-inbox"
        if not inbox.is_dir():
            continue
        for payload_path in sorted(inbox.glob("*.json")):
            try:
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                # Leave malformed/inaccessible entries for diagnostics/retry.
                continue
            try:
                payload_path.unlink()
            except OSError:
                continue
            yield payload


def file_qr_data(item: dict[str, Any]) -> str:
    """Read file data into a representation suitable for QR generation.

    Text is encoded directly. Small binary files use a standard data URI so
    the QR contains the actual bytes as base64 rather than merely a filename.
    """
    path = Path(str(item["path"]))
    data = path.read_bytes()
    if b"\x00" not in data:
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass
    mime_type = str(item.get("mime_type") or "application/octet-stream")
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
