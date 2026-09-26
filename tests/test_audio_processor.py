import math
import struct
import wave
import tempfile
from pathlib import Path
import pytest

from app.audio_processor import AudioProcessor, AudioProcessingError


@pytest.fixture
def processor():
    return AudioProcessor()


@pytest.fixture
def sample_wav(tmp_path):
    wav_path = tmp_path / "synthetic_audio.wav"
    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # 1.5 seconds of 440Hz tone
        for i in range(24000):
            val = int(32767.0 * 0.4 * math.sin(2.0 * math.pi * 440.0 * i / 16000))
            wf.writeframes(struct.pack("<h", val))
    return wav_path


def test_supported_formats(processor):
    assert processor.is_supported_format("audio.mp3") is True
    assert processor.is_supported_format("voice.wav") is True
    assert processor.is_supported_format("clip.m4a") is True
    assert processor.is_supported_format("track.flac") is True
    assert processor.is_supported_format("sound.ogg") is True
    assert processor.is_supported_format("recording.webm") is True
    assert processor.is_supported_format("video.mp4") is True
    assert processor.is_supported_format("notes.txt") is False
    assert processor.is_supported_format("binary.exe") is False


def test_convert_to_wav(processor, sample_wav, tmp_path):
    out_wav = tmp_path / "converted.wav"
    result = processor.convert_to_wav(sample_wav, out_wav)
    assert result.exists()
    assert result.stat().st_size > 0

    with wave.open(str(result), "r") as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == 16000
        assert wf.getsampwidth() == 2


def test_get_audio_info(processor, sample_wav):
    info = processor.get_audio_info(sample_wav)
    assert info["filename"] == "synthetic_audio.wav"
    assert info["format"] == "wav"
    assert info["file_size_bytes"] > 0
    assert info["duration_seconds"] >= 1.0


def test_convert_nonexistent_file_raises_error(processor, tmp_path):
    missing_path = tmp_path / "does_not_exist.mp3"
    with pytest.raises(AudioProcessingError):
        processor.convert_to_wav(missing_path)
