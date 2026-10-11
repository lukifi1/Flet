import hashlib
import secrets
from pathlib import Path

from app.core.transfer.payload import (
    DataFrame,
    MetaFrame,
    decode_frame,
    encode_data,
    encode_meta,
)

DEFAULT_CHUNK_SIZE = 400  # bytes per QR code before Base64


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

    def add(self, text):
        """Add one scanned string. Returns True if it was new."""
        frame = decode_frame(text)

        if self.transfer_id is None:
            self.transfer_id = frame.transfer_id
        if frame.transfer_id != self.transfer_id:
            return False  # belongs to another transfer
        self.total = frame.total

        if isinstance(frame, MetaFrame):
            if self.meta is not None:
                return False
            self.meta = frame
            return True

        if frame.index in self.chunks:
            return False  # duplicate
        self.chunks[frame.index] = frame.data
        return True

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
        return data