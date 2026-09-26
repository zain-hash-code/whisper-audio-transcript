"""
Server Launcher Script.
Launches the FastAPI Audio Transcription Studio and opens it in the browser.
"""
import sys
import webbrowser
import threading
import time
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

import uvicorn


def open_browser(port: int = 8000):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[+] Opening Audio Transcription Studio in your browser: {url}\n")
    webbrowser.open(url)


if __name__ == "__main__":
    port = 8000
    host = "127.0.0.1"

    # Start browser opener in background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    print("=" * 65)
    print("      AUDIO TRANSCRIPTION STUDIO IS STARTING")
    print(f"      Server running at: http://{host}:{port}")
    print("      Press Ctrl+C to stop the server anytime.")
    print("=" * 65)

    uvicorn.run("app.main:app", host=host, port=port, log_level="info", reload=False)

