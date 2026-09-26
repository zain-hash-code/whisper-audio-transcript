"""
Transcription format exporters: Plain Text, SRT, WebVTT, and JSON.
"""
import json
from typing import List, Dict, Any


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp: HH:MM:SS,mmm"""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    total_ms %= 3600000
    minutes = total_ms // 60000
    total_ms %= 60000
    secs = total_ms // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp: HH:MM:SS.mmm"""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    total_ms %= 3600000
    minutes = total_ms // 60000
    total_ms %= 60000
    secs = total_ms // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def export_txt(transcript_data: Dict[str, Any], include_timestamps: bool = False) -> str:
    """Export transcription as plain text."""
    if not include_timestamps:
        return transcript_data.get("text", "").strip()

    segments = transcript_data.get("segments", [])
    lines = []
    for seg in segments:
        start_str = format_timestamp_vtt(seg["start"])
        end_str = format_timestamp_vtt(seg["end"])
        lines.append(f"[{start_str} -> {end_str}] {seg['text'].strip()}")
    return "\n".join(lines)


def export_srt(transcript_data: Dict[str, Any]) -> str:
    """Export transcription as SubRip (.srt) subtitles."""
    segments = transcript_data.get("segments", [])
    srt_entries = []
    for idx, seg in enumerate(segments, start=1):
        start = format_timestamp_srt(seg["start"])
        end = format_timestamp_srt(seg["end"])
        text = seg["text"].strip()
        srt_entries.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_entries)


def export_vtt(transcript_data: Dict[str, Any]) -> str:
    """Export transcription as WebVTT (.vtt) format."""
    segments = transcript_data.get("segments", [])
    vtt_lines = ["WEBVTT\n"]
    for seg in segments:
        start = format_timestamp_vtt(seg["start"])
        end = format_timestamp_vtt(seg["end"])
        text = seg["text"].strip()
        vtt_lines.append(f"{start} --> {end}\n{text}\n")
    return "\n".join(vtt_lines)


def export_json(transcript_data: Dict[str, Any]) -> str:
    """Export transcription as structured JSON string."""
    return json.dumps(transcript_data, indent=2, ensure_ascii=False)
