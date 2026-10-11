import os
import random

import pytest
import qrcode
import qrcode.constants

from app.core.transfer.chunker import IntegrityError, Reassembler, build_frames
from app.core.transfer.payload import PayloadError, decode_frame


@pytest.mark.parametrize("size", [0, 1, 399, 400, 401, 5000])
def test_roundtrip(size):
    data = os.urandom(size)
    r = Reassembler()
    for frame in build_frames(data, "test.bin"):
        r.add(frame)
    assert r.is_complete
    assert r.assemble() == data


def test_shuffled_with_duplicates():
    data = os.urandom(3000)
    frames = build_frames(data, "ä ö.txt", chunk_size=250)
    frames = frames + frames[:5]
    random.shuffle(frames)

    r = Reassembler()
    for frame in frames:
        r.add(frame)
    assert r.assemble() == data
    assert r.meta.filename == "ä ö.txt"


def test_missing_chunk():
    frames = build_frames(os.urandom(2000), "x.bin", chunk_size=400)
    r = Reassembler()
    for frame in frames:
        if frame.startswith("FLT1|D|") and frame.split("|")[3] == "2":
            continue  # skip chunk 2
        r.add(frame)
    assert r.missing() == [2]
    with pytest.raises(IntegrityError):
        r.assemble()


def test_wrong_data_is_detected():
    frames = build_frames(os.urandom(1000), "x.bin", transfer_id="abcd1234")
    other = build_frames(os.urandom(1000), "x.bin", transfer_id="abcd1234")
    frames[1] = other[1]  # chunk 0 from a different file

    r = Reassembler()
    for frame in frames:
        r.add(frame)
    with pytest.raises(IntegrityError):
        r.assemble()


def test_other_transfer_is_ignored():
    a = build_frames(b"a" * 900, "a.txt", transfer_id="aaaa0001")
    b = build_frames(b"b" * 900, "b.txt", transfer_id="bbbb0002")
    r = Reassembler()
    for frame in a:
        r.add(frame)
    assert r.add(b[1]) is False
    assert r.assemble() == b"a" * 900


def test_garbage_is_rejected():
    with pytest.raises(PayloadError):
        decode_frame("https://example.com")
    with pytest.raises(PayloadError):
        decode_frame("FLT1|D|abc|notanumber|3|AAAA")


def test_frames_fit_in_qr_code():
    for frame in build_frames(os.urandom(2000), "x.bin"):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(frame)
        qr.make(fit=True)  # raises an error if the frame is too big