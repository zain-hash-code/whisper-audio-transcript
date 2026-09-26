import math
import struct
import wave
import pytest

from app.transcriber import engine


@pytest.fixture
def sample_audio(tmp_path):
    wav_path = tmp_path / "speech_test.wav"
    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # 2 seconds of modulated audio
        for i in range(32000):
            val = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * 300.0 * i / 16000))
            wf.writeframes(struct.pack("<h", val))
    return wav_path


def test_model_loading():
    model = engine.get_model("tiny")
    assert model is not None
    # Test model caching
    cached_model = engine.get_model("tiny")
    assert cached_model is model


def test_transcribe_sample_audio(sample_audio):
    result = engine.transcribe(
        audio_file_path=sample_audio,
        model_name="tiny",
        beam_size=1,
        vad_filter=False
    )
    assert isinstance(result, dict)
    assert "text" in result
    assert "language" in result
    assert "duration" in result
    assert "processing_time" in result
    assert "segments" in result
    assert result["model_used"] == "tiny"
