"""
Speech-to-Text Engine powered by faster-whisper (CTranslate2).
Optimized for 100% computational efficiency with INT8 quantization,
model caching, and Voice Activity Detection (VAD).
"""
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from faster_whisper import WhisperModel

from app.config import DEFAULT_MODEL, AVAILABLE_MODELS
from app.audio_processor import AudioProcessor


class TranscriptionEngine:
    """Manages Whisper models and performs high-speed, accurate speech-to-text."""

    def __init__(self, device: str = "cpu", compute_type: str = "int8"):
        self.device = device
        self.compute_type = compute_type
        self._models: Dict[str, WhisperModel] = {}
        self.audio_processor = AudioProcessor()

    def get_model(self, model_name: str = DEFAULT_MODEL) -> WhisperModel:
        """
        Retrieve or lazy-load the requested Whisper model.
        Cached in memory to eliminate re-loading overhead on subsequent requests.
        """
        if model_name not in AVAILABLE_MODELS:
            model_name = DEFAULT_MODEL

        cache_key = f"{model_name}_{self.device}_{self.compute_type}"
        if cache_key not in self._models:
            print(f"[Transcriber] Loading model '{model_name}' on {self.device} ({self.compute_type})...")
            model = WhisperModel(
                model_name,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
                num_workers=1
            )
            self._models[cache_key] = model
            print(f"[Transcriber] Model '{model_name}' loaded successfully.")

        return self._models[cache_key]

    def transcribe(
        self,
        audio_file_path: str | Path,
        model_name: str = DEFAULT_MODEL,
        language: Optional[str] = None,
        task: str = "transcribe",
        beam_size: int = 5,
        word_timestamps: bool = True,
        vad_filter: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file with high accuracy and speed.
        
        Args:
            audio_file_path: Path to any audio or video file.
            model_name: "tiny", "base", "small", "medium".
            language: Language code (e.g. 'en', 'es', 'fr', 'de') or None for auto-detection.
            task: "transcribe" or "translate" (translates to English).
            beam_size: Beam search width (5 is standard, 1 is ultra-fast).
            word_timestamps: Whether to extract word-level timing offsets.
            vad_filter: Voice Activity Detection to skip silence and speed up transcription.
        """
        start_time = time.time()
        file_path = Path(audio_file_path)

        # Standardize audio using AudioProcessor
        # Convert any input format (mp3, m4a, webm, etc.) to 16kHz mono WAV
        converted_wav = self.audio_processor.convert_to_wav(file_path)

        try:
            model = self.get_model(model_name)

            # Clean language param if 'auto' or empty
            lang_param = language if language and language.strip() and language.strip().lower() != "auto" else None

            segments_generator, info = model.transcribe(
                str(converted_wav),
                language=lang_param,
                task=task,
                beam_size=beam_size,
                word_timestamps=word_timestamps,
                vad_filter=vad_filter,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            # Consume the generator into segment list
            segments_list = []
            full_text_parts = []

            for idx, segment in enumerate(segments_generator):
                seg_text = segment.text.strip()
                full_text_parts.append(seg_text)

                words_data = []
                if word_timestamps and segment.words:
                    for w in segment.words:
                        words_data.append({
                            "word": w.word,
                            "start": round(w.start, 2),
                            "end": round(w.end, 2),
                            "probability": round(w.probability, 2)
                        })

                segments_list.append({
                    "id": idx + 1,
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": seg_text,
                    "words": words_data
                })

            full_text = " ".join(full_text_parts)
            proc_time = round(time.time() - start_time, 2)

            return {
                "text": full_text,
                "language": info.language,
                "language_probability": round(info.language_probability, 3) if info.language_probability else 1.0,
                "duration": round(info.duration, 2) if info.duration else 0.0,
                "processing_time": proc_time,
                "model_used": model_name,
                "task": task,
                "segments": segments_list,
                "word_count": len(full_text.split()) if full_text else 0,
                "character_count": len(full_text)
            }

        finally:
            # Clean up the intermediate WAV file if different from original
            if converted_wav.exists() and converted_wav != file_path:
                try:
                    converted_wav.unlink()
                except OSError:
                    pass


# Singleton engine instance
engine = TranscriptionEngine()
