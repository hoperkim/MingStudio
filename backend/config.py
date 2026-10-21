"""MingStudio Configuration & Constants
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
MING_MODEL_DIR = MODELS_DIR / "Ming-3.0-tts-tiny"
OUTPUTS_DIR = DATA_DIR / "outputs"
REFERENCES_DIR = DATA_DIR / "references"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure runtime directories exist safely
for d in [DATA_DIR, MODELS_DIR, MING_MODEL_DIR, OUTPUTS_DIR, REFERENCES_DIR]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# Hugging Face Model Specs
HF_REPO_ID = "inclusionAI/Ming-3.0-tts-tiny"
HF_BASE_URL = f"https://huggingface.co/{HF_REPO_ID}/resolve/main"

TOTAL_SHARDS = 30
EXPECTED_SAFETENSORS = [
    f"model-{i:05d}-of-00030.safetensors" for i in range(1, TOTAL_SHARDS + 1)
]

ESSENTIAL_CONFIG_FILES = [
    "config.json",
    "generation_config.json",
    "model.safetensors.index.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "prompt_contract.py",
    "modeling_lingv3_tts.py",
    "modeling_bailing_moe_v3.py",
    "modeling_audio_vae.py",
    "configuration_lingv3_tts.py",
    "configuration_bailing_moe_v3.py",
    "configuration_audio_vae.py",
    "aggregator.py",
    "flowloss.py",
    "CFM.py",
    "dit.py",
    "mlp.py",
    "modules.py",
    "vae_modules.py",
    "fm_utils.py",
    "istft.py"
]

TOTAL_EXPECTED_BYTES = 18_006_571_994  # ~16.76 GiB

# Network & Server
DEFAULT_PORT = 4100
MAX_PORT_SEARCH = 4150

# 7 Supported Languages
SUPPORTED_LANGUAGES = [
    {
        "code": "ko",
        "name": "한국어",
        "native": "한국어",
        "flag": "🇰🇷",
        "sample": "안녕하세요! Ming-3.0 MoE AI 음성 작업실에 오신 것을 환영합니다. [laugh] 멋진 하루 되세요!"
    },
    {
        "code": "zh",
        "name": "중국어",
        "native": "中文",
        "flag": "🇨🇳",
        "sample": "您好！欢迎使用 Ming-3.0 MoE AI 语音工作站。[laugh] 今天过得怎么样？"
    },
    {
        "code": "en",
        "name": "영어",
        "native": "English",
        "flag": "🇺🇸",
        "sample": "Hello! Welcome to MingStudio AI Voice Workstation. [laugh] It is wonderful to meet you today."
    },
    {
        "code": "ja",
        "name": "일본어",
        "native": "日本語",
        "flag": "🇯🇵",
        "sample": "こんにちは！Ming-3.0 AI 音声ワークステーションへようこそ。[laugh] 今日も素敵な一日をお過ごしください。"
    },
    {
        "code": "es",
        "name": "스페인어",
        "native": "Español",
        "flag": "🇪🇸",
        "sample": "¡Hola! Bienvenido a la estación de trabajo vocal MingStudio AI. [laugh] ¡Que tengas un gran día!"
    },
    {
        "code": "fr",
        "name": "프랑스어",
        "native": "Français",
        "flag": "🇫🇷",
        "sample": "Bonjour ! Bienvenue dans le studio vocal MingStudio IA. [laugh] Passez une excellente journée !"
    },
    {
        "code": "de",
        "name": "독일어",
        "native": "Deutsch",
        "flag": "🇩🇪",
        "sample": "Hallo! Willkommen in der MingStudio KI-Sprach-Workstation. [laugh] Einen wunderschönen Tag noch!"
    }
]

# 14 Paralinguistic Emotion Control Tags
PARALINGUISTIC_TAGS = [
    {"tag": "[laugh]", "name": "웃음", "desc": "자연스러운 웃음", "icon": "😄", "alt": "[Laughter]"},
    {"tag": "[sigh]", "name": "한숨", "desc": "안도 또는 탄식의 한숨", "icon": "😮‍💨", "alt": "[Sigh]"},
    {"tag": "[whisper]", "name": "속삭임", "desc": "조용한 귓속말", "icon": "🤫", "alt": "[Whisper]"},
    {"tag": "[angry]", "name": "분노", "desc": "격앙된 감정", "icon": "😠", "alt": "[Angry]"},
    {"tag": "[gasp]", "name": "숨들이쉼", "desc": "놀라서 들이쉬는 숨", "icon": "🫢", "alt": "[Breathing]"},
    {"tag": "[cry]", "name": "울음", "desc": "눈물 섞인 흐느낌", "icon": "😢", "alt": "[Sob]"},
    {"tag": "[cough]", "name": "기침", "desc": "가벼운 헛기침 소리", "icon": "😷", "alt": "[Cough]"},
    {"tag": "[clear-throat]", "name": "목가다듬기", "desc": "목소리 정돈 흠흠", "icon": "🗣️", "alt": "[Clear-Throat]"},
    {"tag": "[yawn]", "name": "하품", "desc": "나른한 하품", "icon": "🥱", "alt": "[Yawn]"},
    {"tag": "[pant]", "name": "헐떡임", "desc": "가쁜 호흡", "icon": "🫁", "alt": "[Pant]"},
    {"tag": "[sneeze]", "name": "재채기", "desc": "돌발 에취 재채기", "icon": "🤧", "alt": "[Sneeze]"},
    {"tag": "[chuckle]", "name": "킬킬", "desc": "나직하게 터지는 웃음", "icon": "🤭", "alt": "[Chuckle]"},
    {"tag": "[snicker]", "name": "낄낄", "desc": "장난스러운 비웃음", "icon": "😏", "alt": "[Snicker]"},
    {"tag": "[uhm]", "name": "망설임", "desc": "생각하듯 머뭇거림", "icon": "🤔", "alt": "[Uhm]"}
]
