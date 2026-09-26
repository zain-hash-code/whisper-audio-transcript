"""
FastAPI Backend Application for the Audio Transcription System.
Provides RESTful APIs for file uploads, live voice recording uploads,
model management, and subtitle/text exports.
"""
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    UPLOAD_DIR,
    SAMPLES_DIR,
    STATIC_DIR,
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    SUPPORTED_EXTENSIONS,
    FFMPEG_PATH
)
from app.audio_processor import AudioProcessor, AudioProcessingError
from app.transcriber import engine
from app import exporters

app = FastAPI(
    title="Audio Transcription System",
    description="High-efficiency speech-to-text platform supporting all audio formats and live mic input.",
    version="1.0.0"
)

# Enable CORS for local development and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static web UI assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount samples for quick-testing demo audio
if SAMPLES_DIR.exists():
    app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

audio_processor = AudioProcessor()


@app.get("/api/samples")
async def get_demo_samples():
    """List available demo audio files for 1-click testing."""
    samples = []
    if SAMPLES_DIR.exists():
        for p in SAMPLES_DIR.glob("*.*"):
            if p.suffix.lower() in [".mp3", ".m4a", ".wav", ".ogg", ".flac", ".webm"]:
                samples.append({
                    "filename": p.name,
                    "url": f"/samples/{p.name}",
                    "format": p.suffix.lstrip(".").upper(),
                    "size_mb": round(p.stat().st_size / (1024 * 1024), 2)
                })
    return {"samples": samples}


@app.get("/")
async def root():
    """Serve the primary user interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Audio Transcription API is online. UI index.html not yet built."}


@app.get("/api/health")
async def health_check():
    """System health check and environmental status."""
    return {
        "status": "healthy",
        "ffmpeg_available": Path(FFMPEG_PATH).exists() or shutil.which("ffmpeg") is not None,
        "ffmpeg_path": FFMPEG_PATH,
        "default_model": DEFAULT_MODEL,
        "supported_extensions": sorted(list(SUPPORTED_EXTENSIONS)),
        "loaded_models": list(engine._models.keys())
    }


@app.get("/api/models")
async def list_models():
    """Return available Whisper model presets."""
    return {
        "default": DEFAULT_MODEL,
        "models": AVAILABLE_MODELS
    }


@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL),
    language: Optional[str] = Form(None),
    task: str = Form("transcribe"),
    word_timestamps: bool = Form(True),
    beam_size: int = Form(5)
):
    """
    Transcribe any uploaded voice or video file into text.
    Handles almost all formats: MP3, WAV, M4A, OGG, WEBM, FLAC, MP4, etc.
    """
    filename = file.filename or "audio.wav"
    suffix = Path(filename).suffix.lower()

    # If file was recorded from browser microphone without extension, default to .webm or .wav
    if not suffix:
        suffix = ".webm"
        filename += suffix

    # Save uploaded file safely to temporary disk location
    temp_input = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, dir=UPLOAD_DIR, delete=False) as tmp:
            temp_input = Path(tmp.name)
            shutil.copyfileobj(file.file, tmp)

        # Transcribe using faster-whisper engine
        result = engine.transcribe(
            audio_file_path=temp_input,
            model_name=model,
            language=language,
            task=task,
            beam_size=beam_size,
            word_timestamps=word_timestamps
        )

        result["filename"] = file.filename
        return result

    except AudioProcessingError as ape:
        raise HTTPException(status_code=400, detail=str(ape))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clean up temporary uploaded file
        if temp_input and temp_input.exists():
            try:
                temp_input.unlink()
            except OSError:
                pass


@app.post("/api/export")
async def export_transcript(
    data: dict,
    format: str = Query(..., pattern="^(txt|txt_timestamps|srt|vtt|json)$"),
    filename: Optional[str] = Query("transcript")
):
    """
    Export transcription data in TXT, SRT, VTT, or JSON format.
    """
    safe_name = Path(filename).stem or "transcript"

    if format == "txt":
        content = exporters.export_txt(data, include_timestamps=False)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.txt"'}
        )
    elif format == "txt_timestamps":
        content = exporters.export_txt(data, include_timestamps=True)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_timestamped.txt"'}
        )
    elif format == "srt":
        content = exporters.export_srt(data)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.srt"'}
        )
    elif format == "vtt":
        content = exporters.export_vtt(data)
        return Response(
            content=content,
            media_type="text/vtt; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.vtt"'}
        )
    elif format == "json":
        content = exporters.export_json(data)
        return Response(
            content=content,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.json"'}
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
