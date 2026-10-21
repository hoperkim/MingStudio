"""MingStudio FastAPI Application Server
Provides Same-Origin static serving, REST endpoints, SSE telemetry streaming,
smart port binding, and native Edge App mode launching.
"""

import os
import sys
import time
import socket
import json
import shutil
import subprocess
import threading
import argparse
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure stdout/stderr handle UTF-8 cleanly on Windows CP949
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Setup import paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.config import (
        BASE_DIR,
        FRONTEND_DIR,
        OUTPUTS_DIR,
        REFERENCES_DIR,
        DEFAULT_PORT,
        MAX_PORT_SEARCH,
        SUPPORTED_LANGUAGES,
        PARALINGUISTIC_TAGS
    )
    from backend.model_manager import check_model_status, get_gpu_info
    from backend.downloader import downloader_instance
    from backend.voice_engine import engine_instance
except ImportError:
    from config import (
        BASE_DIR,
        FRONTEND_DIR,
        OUTPUTS_DIR,
        REFERENCES_DIR,
        DEFAULT_PORT,
        MAX_PORT_SEARCH,
        SUPPORTED_LANGUAGES,
        PARALINGUISTIC_TAGS
    )
    from model_manager import check_model_status, get_gpu_info
    from downloader import downloader_instance
    from voice_engine import engine_instance


app = FastAPI(
    title="MingStudio AI Voice Workstation",
    description="MoE AI Voice Workstation with 7 Languages and 14 Paralinguistic Tags",
    version="3.0.0"
)

# CORS middleware for universal local accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount outputs and references for direct streaming and WaveSurfer playback
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/references", StaticFiles(directory=str(REFERENCES_DIR)), name="references")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# Pydantic Request Models
class TTSGenerateRequest(BaseModel):
    text: str
    language: str = "ko"
    speed: float = 1.0
    pitch: float = 0.0
    emotion: str = "neutral"
    voice_design_prompt: str = ""
    reference_audio_id: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve frontend index.html with Same-Origin security guarantee."""
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="frontend/index.html not found")
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


@app.post("/api/shutdown")
async def shutdown_studio():
    """Safely terminate the MingStudio server process."""
    def delayed_exit():
        time.sleep(0.6)
        print("[MingStudio] Shutdown requested by user. Exiting safely.")
        os._exit(0)

    threading.Thread(target=delayed_exit, daemon=True).start()
    return {"status": "shutting_down", "message": "MingStudio is shutting down"}


@app.get("/api/health")
async def health_check():
    """Health check used by launcher to confirm server readiness."""
    return {
        "status": "ok",
        "app": "MingStudio",
        "version": "3.0.0",
        "timestamp": time.time()
    }


@app.get("/api/config")
async def get_studio_config():
    """Return studio configuration, languages, and 14 paralinguistic tags."""
    return {
        "languages": SUPPORTED_LANGUAGES,
        "paralinguistic_tags": PARALINGUISTIC_TAGS,
        "default_port": DEFAULT_PORT,
        "gpu": get_gpu_info()
    }


@app.get("/api/model/status")
async def get_model_status():
    """Preflight check: returns model presence, 30 safetensors status, and hardware telemetry."""
    return check_model_status()


@app.post("/api/model/download/start")
async def start_model_download():
    """Trigger 8-thread background download of Ming-3.0-tts-tiny."""
    success = downloader_instance.start()
    return {
        "success": success,
        "message": "Download initiated" if success else "Download already in progress"
    }


@app.get("/api/model/download/progress")
async def get_download_progress():
    """Return snapshot of download telemetry (MB/s, ETA, % completed)."""
    return downloader_instance.get_progress()


@app.get("/api/model/download/stream")
async def stream_download_progress(request: Request):
    """Server-Sent Events (SSE) streaming progress updates every 200ms."""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            progress = downloader_instance.get_progress()
            data_json = json.dumps(progress, ensure_ascii=False)
            yield f"data: {data_json}\n\n"
            if progress["status"] in ["completed", "error", "cancelled"]:
                break
            time.sleep(0.2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/model/download/cancel")
async def cancel_model_download():
    """Cancel currently active download."""
    downloader_instance.cancel()
    return {"status": "cancelled", "message": "Download cancelled by user"}


@app.post("/api/tts/generate")
async def generate_speech(req: TTSGenerateRequest):
    """Render speech audio with emotion, pitch, speed, and paralinguistic markers."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")

    result = engine_instance.generate(
        text=req.text,
        language=req.language,
        speed=req.speed,
        pitch=req.pitch,
        emotion=req.emotion,
        voice_design_prompt=req.voice_design_prompt,
        reference_audio_id=req.reference_audio_id
    )
    return result


@app.post("/api/voice/clone/upload")
async def upload_reference_audio(file: UploadFile = File(...)):
    """Upload short reference audio file for Zero-Shot voice cloning."""
    allowed_exts = [".wav", ".mp3", ".m4a", ".ogg", ".flac"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"지원되지 않는 오디오 형식입니다. 허용 형식: {', '.join(allowed_exts)}"
        )

    ref_id = f"ref_{int(time.time())}_{uuid.uuid4().hex[:6]}{ext}"
    dest_path = REFERENCES_DIR / ref_id

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "reference_id": ref_id,
        "original_name": file.filename,
        "url": f"/references/{ref_id}",
        "size_bytes": dest_path.stat().st_size
    }


@app.get("/api/history")
async def get_history():
    """Retrieve history of rendered audio clips."""
    return engine_instance.get_history()


@app.delete("/api/history/{filename}")
async def delete_history_item(filename: str):
    """Delete audio file from history."""
    file_path = OUTPUTS_DIR / filename
    if file_path.exists():
        file_path.unlink()

    # Update history.json
    history_file = OUTPUTS_DIR / "history.json"
    if history_file.exists():
        try:
            items = json.loads(history_file.read_text(encoding="utf-8"))
            items = [item for item in items if item.get("filename") != filename]
            history_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    return {"status": "deleted", "filename": filename}


# Smart Port Binding & Native Launcher Utilities
def find_available_port(start_port: int = DEFAULT_PORT, max_port: int = MAX_PORT_SEARCH) -> int:
    """Find the first available TCP port in the specified range."""
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def wait_for_server(port: int, timeout_sec: float = 12.0) -> bool:
    """Poll the /api/health endpoint until the backend is fully initialized."""
    import urllib.request
    url = f"http://127.0.0.1:{port}/api/health"
    start_t = time.time()
    while time.time() - start_t < timeout_sec:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MingStudio/Launcher"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def launch_native_browser(url: str):
    """Launch Microsoft Edge in App Mode for a frameless native application experience."""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("msedge.exe") or ""
    ]
    for p in edge_paths:
        if p and os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={url}"])
                print(f"[Launcher] Launched Microsoft Edge in App Mode: {url}")
                return
            except Exception:
                pass

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("chrome.exe") or ""
    ]
    for p in chrome_paths:
        if p and os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={url}"])
                print(f"[Launcher] Launched Chrome in App Mode: {url}")
                return
            except Exception:
                pass

    # Fallback to default browser
    webbrowser.open(url)
    print(f"[Launcher] Opened standard browser: {url}")


def main():
    parser = argparse.ArgumentParser(description="MingStudio Server Launcher")
    parser.add_argument("--port", type=int, default=None, help="Port to bind server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    parser.add_argument("--launch-browser", action="store_true", help="Launch Edge App mode when ready")
    args = parser.parse_args()

    port = args.port or find_available_port(DEFAULT_PORT)
    app_url = f"http://127.0.0.1:{port}"

    print("=" * 64)
    print(" [MingStudio] (Ming-3.0 MoE AI Voice Workstation)")
    print("=" * 64)
    print(f" ▶ Local Address: {app_url}")
    print(f" ▶ Backend Mode : Native FastAPI Same-Origin")
    print(f" ▶ Base Directory: {BASE_DIR}")
    print("=" * 64)

    if args.launch_browser:
        def background_launcher():
            if wait_for_server(port):
                launch_native_browser(app_url)
            else:
                print("[Launcher] Timeout waiting for backend to become ready.")

        launcher_thread = threading.Thread(target=background_launcher, daemon=True)
        launcher_thread.start()

    uvicorn.run(app, host=args.host, port=port, log_level="info")


if __name__ == "__main__":
    main()
