"""
Audio processing and normalization utilities using FFmpeg.
Supports converting nearly all audio and video formats to standardized 16kHz mono WAV.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from app.config import FFMPEG_PATH, SUPPORTED_EXTENSIONS


class AudioProcessingError(Exception):
    """Raised when audio conversion or probing fails."""
    pass


class AudioProcessor:
    """Handles audio conversion, normalization, and metadata extraction."""

    def __init__(self, ffmpeg_bin: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_bin or FFMPEG_PATH

    def is_supported_format(self, filename_or_ext: str) -> bool:
        """Check if the given filename or extension is in the supported set."""
        suffix = Path(filename_or_ext).suffix.lower()
        return suffix in SUPPORTED_EXTENSIONS

    def convert_to_wav(self, input_path: str | Path, output_path: Optional[str | Path] = None) -> Path:
        """
        Convert any input audio/video file to 16kHz mono 16-bit PCM WAV.
        Whisper performs optimally and fastest on 16kHz mono audio.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise AudioProcessingError(f"Input file not found: {input_path}")

        if output_path is None:
            # Create a temporary output file with .wav suffix
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            output_path = Path(tmp.name)
        else:
            output_path = Path(output_path)

        # Build FFmpeg command:
        # -y: overwrite output
        # -i <input>: input file
        # -vn: skip video streams
        # -acodec pcm_s16le: 16-bit PCM WAV
        # -ar 16000: 16kHz sample rate
        # -ac 1: mono audio
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", str(input_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_path)
        ]

        try:
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            if process.returncode != 0:
                err_msg = process.stderr.decode("utf-8", errors="replace")
                raise AudioProcessingError(f"FFmpeg conversion failed: {err_msg[:300]}")

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise AudioProcessingError("FFmpeg produced an empty or missing output file.")

            return output_path

        except Exception as e:
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass
            raise AudioProcessingError(f"Failed to process audio: {str(e)}")

    def get_audio_info(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Retrieve audio file details like size, format, and estimated duration.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise AudioProcessingError(f"File not found: {file_path}")

        file_size = file_path.stat().st_size
        suffix = file_path.suffix.lower()

        # Simple duration estimation using FFmpeg if possible
        duration = 0.0
        try:
            cmd = [
                self.ffmpeg_bin,
                "-i", str(file_path)
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            stderr_text = proc.stderr.decode("utf-8", errors="replace")
            # Parse Duration: 00:00:00.00
            for line in stderr_text.splitlines():
                if "Duration:" in line:
                    parts = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = parts.split(":")
                    duration = float(h) * 3600 + float(m) * 60 + float(s)
                    break
        except Exception:
            pass

        return {
            "filename": file_path.name,
            "format": suffix.lstrip("."),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "duration_seconds": round(duration, 2)
        }
