"""
Application configuration for the Audio Transcription System.
"""
import os
from pathlib import Path

# Silence HuggingFace symlinks warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES_DIR = BASE_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Supported audio & video extensions
SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".oga", ".opus",
    ".flac", ".webm", ".wma", ".mp4", ".mkv", ".mov", ".avi",
    ".3gp", ".amr", ".aiff", ".caf"
}

# Available Whisper model presets
AVAILABLE_MODELS = {
    "tiny": {
        "name": "Tiny (Fastest)",
        "description": "Ultra-fast transcription (~1s), low memory usage (~400MB)",
        "size": "~75 MB",
        "speed": "Fastest"
    },
    "base": {
        "name": "Base (Balanced)",
        "description": "Great balance between accuracy and high speed (~1GB)",
        "size": "~140 MB",
        "speed": "Fast"
    },
    "small": {
        "name": "Small (Accurate)",
        "description": "High accuracy, handles noisy speech & complex accents (~2GB)",
        "size": "~460 MB",
        "speed": "Moderate"
    },
    "medium": {
        "name": "Medium (Professional)",
        "description": "Professional quality, deep vocabulary comprehension (~5GB)",
        "size": "~1.5 GB",
        "speed": "Slower"
    }
}

DEFAULT_MODEL = "base"

# Locate FFmpeg binary
def get_ffmpeg_path() -> str:
    """Return path to ffmpeg binary, leveraging imageio-ffmpeg or system path."""
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and Path(ffmpeg_exe).exists():
            return ffmpeg_exe
    except Exception:
        pass
    return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_path()
