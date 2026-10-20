# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine import MingEngine, SUPPORTED_LANGUAGES, PARALINGUISTIC_TAGS

app = FastAPI(
    title="MingStudio AI Voice Workstation",
    description="Universal Local MoE TTS Engine (Ming-3.0-tts-tiny) with Zero-Shot Cloning, Voice Design & Video Dubbing",
    version="1.0.0"
)

# Enable CORS for local modern webview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
VOICES_DIR = DATA_DIR / "voices"
OUTPUTS_DIR = DATA_DIR / "outputs"

for d in [DATA_DIR, MODELS_DIR, VOICES_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Initialize Engine
engine = MingEngine(MODELS_DIR)

# Request Models
class SynthesizeRequest(BaseModel):
    text: str
    language: str = "ko"  # ko, zh, en, ja, etc.
    voice_id: Optional[str] = "default"
    voice_description: Optional[str] = None  # Voice Design prompt
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    seed: Optional[int] = 42
    output_format: str = "wav"

class VoiceDesignRequest(BaseModel):
    name: str
    description: str
    sample_text: str = "안녕하세요, 새롭게 디자인된 목소리입니다."
    language: str = "ko"
    gender: str = "female"

@app.get("/api/status")
def get_system_status():
    """Returns GPU, VRAM, engine readiness, and supported languages."""
    return {
        "app_name": "MingStudio",
        "version": "1.0.0",
        "device": engine.device,
        "gpu_name": engine.gpu_name,
        "vram_gb": engine.vram_gb,
        "model_id": engine.model_id,
        "is_model_downloaded": engine.check_model_downloaded(),
        "is_model_loaded": engine.is_loaded,
        "supported_languages": SUPPORTED_LANGUAGES,
        "paralinguistic_tags": PARALINGUISTIC_TAGS
    }

@app.get("/api/languages")
def get_languages():
    """Returns available languages (Korean, Chinese, English, Japanese, etc.)."""
    return SUPPORTED_LANGUAGES

@app.get("/api/tags")
def get_tags():
    """Returns 14 paralinguistic inline tags for one-click insertion."""
    return PARALINGUISTIC_TAGS

@app.get("/api/voices")
def get_saved_voices():
    """Lists saved custom voice profiles and factory presets."""
    voices = [
        {
            "id": "preset_ko_female_calm",
            "name": "차분한 다큐 나레이터",
            "gender": "female",
            "language": "ko",
            "flag": "🇰🇷",
            "description": "20~30대 차분하고 지적인 다큐멘터리/오디오북 나레이션",
            "is_preset": True
        },
        {
            "id": "preset_ko_male_deep",
            "name": "깊은 중저음 스토리텔러",
            "gender": "male",
            "language": "ko",
            "flag": "🇰🇷",
            "description": "신뢰감 있고 깊은 울림의 중저음 남성 해설",
            "is_preset": True
        },
        {
            "id": "preset_en_female_studio",
            "name": "Clara (Studio English)",
            "gender": "female",
            "language": "en",
            "flag": "🇺🇸",
            "description": "Crisp and clear North American studio presenter",
            "is_preset": True
        },
        {
            "id": "preset_zh_female_gentle",
            "name": "小雅 (温柔国语)",
            "gender": "female",
            "language": "zh",
            "flag": "🇨🇳",
            "description": "标准普通话，温和亲切播音级女声",
            "is_preset": True
        },
        {
            "id": "preset_ja_female_anime",
            "name": "ヒカリ (日本語・明瞭)",
            "gender": "female",
            "language": "ja",
            "flag": "🇯🇵",
            "description": "明るく聞き取りやすい標準日本語ナレーション",
            "is_preset": True
        }
    ]
    
    # Read custom cloned profiles
    profile_meta = VOICES_DIR / "profiles.json"
    if profile_meta.exists():
        try:
            with open(profile_meta, "r", encoding="utf-8") as f:
                custom = json.load(f)
                voices.extend(custom)
        except Exception:
            pass
            
    return voices

@app.post("/api/clone")
async def clone_voice(
    name: str = Form(...),
    language: str = Form("ko"),
    description: str = Form(""),
    audio_file: UploadFile = File(...)
):
    """Zero-shot voice cloning from a 5-30 second audio clip."""
    safe_id = f"custom_{int(time.time())}"
    ext = Path(audio_file.filename).suffix or ".wav"
    audio_save_path = VOICES_DIR / f"{safe_id}{ext}"
    
    with open(audio_save_path, "wb") as f:
        shutil.copyfileobj(audio_file.file, f)
        
    new_profile = {
        "id": safe_id,
        "name": name,
        "language": language,
        "flag": SUPPORTED_LANGUAGES.get(language, {}).get("flag", "🌐"),
        "description": description or f"클론된 음성 샘플 ({audio_file.filename})",
        "audio_path": str(audio_save_path),
        "is_preset": False,
        "created_at": time.time()
    }
    
    meta_path = VOICES_DIR / "profiles.json"
    existing = []
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
            
    existing.append(new_profile)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
        
    return {"status": "success", "profile": new_profile}

@app.post("/api/generate")
def generate_speech(req: SynthesizeRequest):
    """
    Main speech generation endpoint.
    Supports languages (ko, zh, en, ja), inline paralinguistic tags, and voice design.
    """
    timestamp = int(time.time() * 1000)
    out_filename = f"ming_speech_{timestamp}.{req.output_format}"
    out_path = OUTPUTS_DIR / out_filename
    
    # Generate speech
    result = engine.generate_speech(
        text=req.text,
        language=req.language,
        voice_id=req.voice_id,
        voice_description=req.voice_description,
        speed=req.speed,
        pitch=req.pitch,
        volume=req.volume,
        seed=req.seed,
        output_format=req.output_format
    )
    
    # If the model is not fully downloaded, create fallback/notice or render
    return {
        "status": "success",
        "audio_url": f"/api/audio/{out_filename}",
        "filename": out_filename,
        "meta": result
    }

@app.get("/api/audio/{filename}")
def stream_audio(filename: str):
    """Streams generated audio file."""
    path = OUTPUTS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    media_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
    return FileResponse(str(path), media_type=media_type)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=4100, reload=False)
