import base64
from dataclasses import dataclass

# Meta frame: FLT1|M|transfer_id|total|size|sha256|filename
# Data frame: FLT1|D|transfer_id|index|total|data
# (filename and data are Base64 text)

MAGIC = "FLT1"
SEP = "|"


class PayloadError(ValueError):
    pass


@dataclass
class MetaFrame:
    transfer_id: str
    total: int
    size: int
    sha256: str
    filename: str


@dataclass
class DataFrame:
    transfer_id: str
    index: int
    total: int
    data: bytes


def _to_b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _from_b64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text)


def encode_meta(meta: MetaFrame) -> str:
    return SEP.join([
        MAGIC, "M", meta.transfer_id, str(meta.total), str(meta.size),
        meta.sha256, _to_b64(meta.filename.encode("utf-8")),
    ])


def encode_data(frame: DataFrame) -> str:
    return SEP.join([
        MAGIC, "D", frame.transfer_id, str(frame.index), str(frame.total),
        _to_b64(frame.data),
    ])


def decode_frame(text: str) -> MetaFrame | DataFrame:
    parts = text.split(SEP)
    if len(parts) < 2 or parts[0] != MAGIC:
        raise PayloadError("not a Flet transfer frame")

    try:
        if parts[1] == "M" and len(parts) == 7:
            return MetaFrame(parts[2], int(parts[3]), int(parts[4]), parts[5],
                             _from_b64(parts[6]).decode("utf-8"))
        if parts[1] == "D" and len(parts) == 6:
            return DataFrame(parts[2], int(parts[3]), int(parts[4]), _from_b64(parts[5]))
    except ValueError as error:
        raise PayloadError(f"broken frame: {error}") from error

    raise PayloadError("unknown frame")