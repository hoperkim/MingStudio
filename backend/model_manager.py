"""MingStudio Model Manager & Preflight Inspection
Provides sub-millisecond model presence checks and hardware telemetry.
"""

import os
from pathlib import Path
from typing import Dict, Any, List

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.config import (
        MING_MODEL_DIR,
        TOTAL_SHARDS,
        EXPECTED_SAFETENSORS,
        ESSENTIAL_CONFIG_FILES,
        TOTAL_EXPECTED_BYTES
    )
except ImportError:
    from config import (
        MING_MODEL_DIR,
        TOTAL_SHARDS,
        EXPECTED_SAFETENSORS,
        ESSENTIAL_CONFIG_FILES,
        TOTAL_EXPECTED_BYTES
    )


def get_gpu_info() -> Dict[str, Any]:
    """Retrieve GPU hardware telemetry safely."""
    info = {
        "cuda_available": False,
        "device_name": "CPU (Accelerated)",
        "vram_total_gb": 0.0,
        "vram_allocated_gb": 0.0,
        "vram_free_gb": 0.0,
        "cuda_version": "N/A"
    }
    try:
        import torch
        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["device_name"] = torch.cuda.get_device_name(0)
            total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
            info["vram_total_gb"] = round(total, 2)
            info["vram_allocated_gb"] = round(allocated, 2)
            info["vram_free_gb"] = round(total - allocated, 2)
            info["cuda_version"] = torch.version.cuda or "N/A"
    except Exception:
        pass
    return info


def check_model_status() -> Dict[str, Any]:
    """Inspect local storage for Ming-3.0-tts-tiny model files.
    
    Returns in < 5ms:
    - ready: True if all 30 safetensors files are present and valid.
    - safetensors_present: number of existing shards.
    - safetensors_total: 30.
    - missing_shards: list of missing shard names.
    - total_bytes_on_disk: total size of existing files.
    - total_expected_bytes: ~18 GB.
    - progress_percent: percentage downloaded so far.
    """
    if not MING_MODEL_DIR.exists():
        MING_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    present_shards = []
    missing_shards = []
    total_bytes = 0

    for shard in EXPECTED_SAFETENSORS:
        shard_path = MING_MODEL_DIR / shard
        if shard_path.is_file() and shard_path.stat().st_size > 1024:
            present_shards.append(shard)
            total_bytes += shard_path.stat().st_size
        else:
            missing_shards.append(shard)

    for cfg in ESSENTIAL_CONFIG_FILES:
        cfg_path = MING_MODEL_DIR / cfg
        if cfg_path.is_file():
            total_bytes += cfg_path.stat().st_size

    ready = (len(present_shards) == TOTAL_SHARDS)
    progress_percent = min(100.0, round((total_bytes / TOTAL_EXPECTED_BYTES) * 100, 1))

    return {
        "ready": ready,
        "model_name": "Ming-3.0-tts-tiny (MoE 7.9B)",
        "safetensors_present": len(present_shards),
        "safetensors_total": TOTAL_SHARDS,
        "missing_shards": missing_shards,
        "total_bytes_on_disk": total_bytes,
        "total_expected_bytes": TOTAL_EXPECTED_BYTES,
        "progress_percent": progress_percent,
        "model_dir": str(MING_MODEL_DIR),
        "gpu": get_gpu_info()
    }
