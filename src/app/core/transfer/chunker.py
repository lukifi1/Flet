import hashlib
import secrets
from pathlib import Path

from app.core.transfer.payload import (
    DataFrame,
    MetaFrame,
    PayloadError,
    decode_frame,
    encode_data,
    encode_meta,
)

DEFAULT_CHUNK_SIZE = 200  # bytes per QR code before Base64
MAX_TRANSFER_SIZE = 50 * 1024 * 1024  # Practical receiver limit: 50 MiB
MAX_CHUNKS = 262_144  # enough for a 50 MiB transfer at the default chunk size


class IntegrityError(Exception):
    pass


def build_frames(data, filename, chunk_size=DEFAULT_CHUNK_SIZE, transfer_id=None):
    """Return a list of strings: first the meta frame, then one frame per chunk."""
    transfer_id = transfer_id or secrets.token_hex(4)
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)] or [b""]

    meta = MetaFrame(transfer_id, len(chunks), len(data),
                     hashlib.sha256(data).hexdigest(), filename)
    frames = [encode_meta(meta)]
    for index, chunk in enumerate(chunks):
        frames.append(encode_data(DataFrame(transfer_id, index, len(chunks), chunk)))
    return frames


def build_frames_from_file(path, chunk_size=DEFAULT_CHUNK_SIZE):
    path = Path(path)
    return build_frames(path.read_bytes(), path.name, chunk_size)


class Reassembler:
    """Receiver side: collects scanned frames and puts the file back together."""

    def __init__(self):
        self.transfer_id = None
        self.meta = None
        self.total = None
        self.chunks = {}  # index -> bytes
        self._received_size = 0

    def add(self, text):
        """Add one scanned string. Returns True if it was new."""
        frame = decode_frame(text)

        if self.transfer_id is None:
            self.transfer_id = frame.transfer_id
        if frame.transfer_id != self.transfer_id:
            return False  # belongs to another transfer

        if isinstance(frame, MetaFrame):
            self._validate_total(frame.total)
            if frame.size < 0 or frame.size > MAX_TRANSFER_SIZE:
                raise PayloadError(f"file exceeds receiver limit of {MAX_TRANSFER_SIZE} bytes")
            if len(frame.sha256) != 64 or any(c not in "0123456789abcdef" for c in frame.sha256.lower()):
                raise PayloadError("invalid SHA-256 in metadata")
            if self.meta is not None:
                if self.meta != frame:
                    raise PayloadError("conflicting metadata for transfer")
                return False
            if self.total is not None and self.total != frame.total:
                raise PayloadError("inconsistent chunk count")
            self.total = frame.total
            self.meta = frame
            return True

        self._validate_total(frame.total)
        if not 0 <= frame.index < frame.total:
            raise PayloadError("chunk index is outside the transfer")
        if self.total is not None and self.total != frame.total:
            raise PayloadError("inconsistent chunk count")
        self.total = frame.total
        if frame.index in self.chunks:
            if self.chunks[frame.index] != frame.data:
                raise PayloadError(f"conflicting duplicate chunk {frame.index}")
            return False  # duplicate
        if self._received_size + len(frame.data) > MAX_TRANSFER_SIZE:
            raise PayloadError(f"file exceeds receiver limit of {MAX_TRANSFER_SIZE} bytes")
        self.chunks[frame.index] = frame.data
        self._received_size += len(frame.data)
        return True

    @staticmethod
    def _validate_total(total):
        if not 1 <= total <= MAX_CHUNKS:
            raise PayloadError(f"invalid chunk count: {total}")

    @property
    def received(self):
        return len(self.chunks)

    def missing(self):
        if self.total is None:
            return []
        return [i for i in range(self.total) if i not in self.chunks]

    @property
    def is_complete(self):
        return self.meta is not None and not self.missing()

    def assemble(self):
        if not self.is_complete:
            raise IntegrityError("transfer is not complete yet")
        data = b"".join(self.chunks[i] for i in range(self.total))
        if hashlib.sha256(data).hexdigest() != self.meta.sha256:
            raise IntegrityError("hash mismatch")
        if len(data) != self.meta.size:
            raise IntegrityError("file size does not match metadata")
        return data

    def save_to(self, path):
        """Assemble, verify, and write the received file to *path*."""
        path = Path(path)
        path.write_bytes(self.assemble())
        return path
