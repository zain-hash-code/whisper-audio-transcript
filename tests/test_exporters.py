import json
import pytest
from app import exporters


@pytest.fixture
def mock_transcript():
    return {
        "text": "Hello world. Welcome to the transcription system.",
        "language": "en",
        "duration": 4.5,
        "segments": [
            {
                "id": 1,
                "start": 0.0,
                "end": 2.1,
                "text": "Hello world."
            },
            {
                "id": 2,
                "start": 2.2,
                "end": 4.5,
                "text": "Welcome to the transcription system."
            }
        ]
    }


def test_export_txt(mock_transcript):
    plain = exporters.export_txt(mock_transcript, include_timestamps=False)
    assert plain == "Hello world. Welcome to the transcription system."

    with_time = exporters.export_txt(mock_transcript, include_timestamps=True)
    assert "[00:00:00.000 -> 00:00:02.100] Hello world." in with_time
    assert "[00:00:02.200 -> 00:00:04.500] Welcome to the transcription system." in with_time


def test_export_srt(mock_transcript):
    srt_out = exporters.export_srt(mock_transcript)
    assert "1\n00:00:00,000 --> 00:00:02,100\nHello world." in srt_out
    assert "2\n00:00:02,200 --> 00:00:04,500\nWelcome to the transcription system." in srt_out


def test_export_vtt(mock_transcript):
    vtt_out = exporters.export_vtt(mock_transcript)
    assert vtt_out.startswith("WEBVTT\n")
    assert "00:00:00.000 --> 00:00:02.100\nHello world." in vtt_out
    assert "00:00:02.200 --> 00:00:04.500\nWelcome to the transcription system." in vtt_out


def test_export_json(mock_transcript):
    json_str = exporters.export_json(mock_transcript)
    loaded = json.loads(json_str)
    assert loaded["language"] == "en"
    assert len(loaded["segments"]) == 2
    assert loaded["segments"][0]["text"] == "Hello world."
