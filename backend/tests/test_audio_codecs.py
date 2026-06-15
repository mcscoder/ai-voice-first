from io import BytesIO

import av
import numpy as np

from app.services.asr import AsrService
from app.services.tts import encode_wav_audio


def encode_m4a(audio: np.ndarray, sample_rate: int) -> bytes:
    output = BytesIO()
    with av.open(output, mode="w", format="mp4") as container:
        stream = container.add_stream("aac", rate=sample_rate)
        stream.layout = "mono"

        frame = av.AudioFrame.from_ndarray(
            audio.reshape(1, -1),
            format="flt",
            layout="mono",
        )
        frame.sample_rate = sample_rate

        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)

    return output.getvalue()


def test_asr_decodes_flutter_m4a_upload() -> None:
    sample_rate = 44100
    audio = np.sin(np.linspace(0, 2 * np.pi, sample_rate, endpoint=False)).astype(
        np.float32
    )
    encoded_audio = encode_m4a(audio, sample_rate)

    decoded_audio, decoded_sample_rate = AsrService().decode_audio_bytes(encoded_audio)

    assert decoded_sample_rate == sample_rate
    assert decoded_audio.dtype == np.float32
    assert decoded_audio.ndim == 1
    assert decoded_audio.size > 0


def test_tts_encodes_wav_with_av() -> None:
    audio = np.zeros(16000, dtype=np.float32)

    encoded_audio = encode_wav_audio(audio, sample_rate=16000)

    with av.open(BytesIO(encoded_audio), mode="r") as container:
        frames = list(container.decode(audio=0))

    assert encoded_audio.startswith(b"RIFF")
    assert frames
    assert frames[0].sample_rate == 16000
