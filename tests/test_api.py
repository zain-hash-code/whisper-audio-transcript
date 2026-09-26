import io
import math
import struct
import wave
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def generate_wav_bytes(duration_sec=1.5):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        num_samples = int(16000 * duration_sec)
        for i in range(num_samples):
            val = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * 400.0 * i / 16000))
            wf.writeframes(struct.pack("<h", val))
    buf.seek(0)
    return buf.read()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["ffmpeg_available"] is True
    assert "wav" in [ext.lstrip(".") for ext in data["supported_extensions"]]


def test_models_endpoint():
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "tiny" in data["models"]
    assert "base" in data["models"]


def test_transcribe_endpoint():
    wav_data = generate_wav_bytes(1.0)
    files = {"file": ("test.wav", wav_data, "audio/wav")}
    data = {"model": "tiny", "beam_size": "1"}

    response = client.post("/api/transcribe", files=files, data=data)
    assert response.status_code == 200
    res_json = response.json()
    assert "text" in res_json
    assert "segments" in res_json
    assert "language" in res_json
    assert "processing_time" in res_json


def test_export_endpoint():
    payload = {
        "text": "Testing export functionality.",
        "language": "en",
        "duration": 2.0,
        "segments": [
            {
                "id": 1,
                "start": 0.0,
                "end": 2.0,
                "text": "Testing export functionality."
            }
        ]
    }

    # Test TXT
    res_txt = client.post("/api/export?format=txt", json=payload)
    assert res_txt.status_code == 200
    assert res_txt.text == "Testing export functionality."

    # Test SRT
    res_srt = client.post("/api/export?format=srt", json=payload)
    assert res_srt.status_code == 200
    assert "00:00:00,000 --> 00:00:02,000" in res_srt.text

    # Test VTT
    res_vtt = client.post("/api/export?format=vtt", json=payload)
    assert res_vtt.status_code == 200
    assert "WEBVTT" in res_vtt.text

    # Test JSON
    res_json = client.post("/api/export?format=json", json=payload)
    assert res_json.status_code == 200
    assert "Testing export functionality." in res_json.text
