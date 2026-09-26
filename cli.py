"""
Command-Line Interface (CLI) for Audio Transcription System.
Transcribe any audio or video file directly from the terminal.
"""
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 console encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.transcriber import engine
from app.audio_processor import AudioProcessor
from app import exporters


def main():
    parser = argparse.ArgumentParser(
        description="Audio Transcription Studio CLI - Transcribe speech from any audio/video format."
    )
    parser.add_argument("input_file", help="Path to the audio or video file to transcribe.")
    parser.add_argument(
        "--model", "-m",
        default="base",
        choices=["tiny", "base", "small", "medium"],
        help="Whisper model preset (default: base)"
    )
    parser.add_argument(
        "--language", "-l",
        default=None,
        help="Spoken language code (e.g., en, es, fr, ur) or leave unset for auto-detection."
    )
    parser.add_argument(
        "--task", "-t",
        default="transcribe",
        choices=["transcribe", "translate"],
        help="transcribe (original) or translate (to English)"
    )
    parser.add_argument(
        "--beam-size", "-b",
        type=int,
        default=5,
        help="Beam size (5 = standard high accuracy, 1 = fastest)"
    )
    parser.add_argument(
        "--export", "-e",
        choices=["txt", "srt", "vtt", "json", "all"],
        default=None,
        help="Export transcription to specified file format(s)."
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Directory to save exported files (defaults to same folder as input file)."
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Analyzing file: {input_path.name}")
    processor = AudioProcessor()
    info = processor.get_audio_info(input_path)
    print(f"    - Size: {info['file_size_mb']} MB")
    print(f"    - Format: {info['format']}")
    if info['duration_seconds']:
        print(f"    - Estimated Duration: {info['duration_seconds']}s")

    print(f"[*] Transcribing using Whisper [{args.model}] (Task: {args.task})...")
    result = engine.transcribe(
        audio_file_path=input_path,
        model_name=args.model,
        language=args.language,
        task=args.task,
        beam_size=args.beam_size
    )

    print("\n" + "=" * 60)
    print(f"TRANSCRIPTION RESULT ({result['language'].upper()} | {result['word_count']} words | {result['processing_time']}s)")
    print("=" * 60)
    print(result["text"])
    print("=" * 60 + "\n")

    # Handle Exports
    if args.export:
        out_dir = Path(args.output_dir) if args.output_dir else input_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = input_path.stem

        formats = ["txt", "srt", "vtt", "json"] if args.export == "all" else [args.export]

        for fmt in formats:
            out_file = out_dir / f"{stem}.{fmt}"
            if fmt == "txt":
                content = exporters.export_txt(result, include_timestamps=False)
            elif fmt == "srt":
                content = exporters.export_srt(result)
            elif fmt == "vtt":
                content = exporters.export_vtt(result)
            elif fmt == "json":
                content = exporters.export_json(result)

            out_file.write_text(content, encoding="utf-8")
            print(f"[+] Saved {fmt.upper()} export: {out_file}")


if __name__ == "__main__":
    main()
