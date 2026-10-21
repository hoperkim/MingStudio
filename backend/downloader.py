"""MingStudio Intelligent 8-Thread Parallel Streaming Downloader
Connects directly to Hugging Face CDN with HTTP Range resume support,
speed estimation (MB/s), and real-time ETA calculation.
"""

import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.config import (
        MING_MODEL_DIR,
        HF_BASE_URL,
        EXPECTED_SAFETENSORS,
        ESSENTIAL_CONFIG_FILES,
        TOTAL_EXPECTED_BYTES
    )
except ImportError:
    from config import (
        MING_MODEL_DIR,
        HF_BASE_URL,
        EXPECTED_SAFETENSORS,
        ESSENTIAL_CONFIG_FILES,
        TOTAL_EXPECTED_BYTES
    )


class ModelDownloader:
    """Thread-safe multi-worker downloader with resumption and real-time telemetry."""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.is_downloading = False
        self.cancel_requested = False
        self.status = "idle"  # idle, downloading, completed, error, cancelled
        self.error_message = ""
        
        # Telemetry metrics
        self.total_bytes = TOTAL_EXPECTED_BYTES
        self.downloaded_bytes = 0
        self.current_speed_mbps = 0.0
        self.eta_seconds = 0
        self.current_files: Dict[str, int] = {}
        self.last_update_time = time.time()
        self.speed_history: list[tuple[float, int]] = []  # (timestamp, bytes)

    def _format_bytes(self, b: int) -> str:
        """Format raw bytes into human readable string."""
        if b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 * 1024 * 1024:
            return f"{b / (1024 * 1024):.1f} MB"
        else:
            return f"{b / (1024 * 1024 * 1024):.2f} GB"

    def _format_eta(self, seconds: int) -> str:
        """Format seconds into localized time string."""
        if seconds <= 0 or seconds > 86400:
            return "계산 중..."
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}시간 {m}분 {s}초 남음"
        elif m > 0:
            return f"{m}분 {s}초 남음"
        else:
            return f"{s}초 남음"

    def get_progress(self) -> Dict[str, Any]:
        """Return current snapshot of download telemetry."""
        with self.lock:
            percent = 0.0
            if self.status == "completed" or (self.total_bytes > 0 and self.downloaded_bytes >= self.total_bytes * 0.99):
                percent = 100.0
            elif self.total_bytes > 0:
                percent = min(99.0, round((self.downloaded_bytes / self.total_bytes) * 100, 1))
            
            eta_str = self._format_eta(self.eta_seconds) if self.is_downloading else ("완료" if self.status == "completed" else "--")
            
            return {
                "status": self.status,
                "is_downloading": self.is_downloading,
                "percent": percent,
                "downloaded_bytes": self.downloaded_bytes,
                "total_bytes": self.total_bytes,
                "downloaded_str": self._format_bytes(self.downloaded_bytes),
                "total_str": self._format_bytes(self.total_bytes),
                "speed_mbps": round(self.current_speed_mbps, 1),
                "eta_seconds": self.eta_seconds,
                "eta_str": eta_str,
                "active_files": list(self.current_files.keys()),
                "error_message": self.error_message
            }

    def _get_remote_file_size(self, url: str) -> Optional[int]:
        """Fetch remote file size via HEAD request."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MingStudio/3.0"}, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                cl = resp.headers.get("Content-Length")
                if cl:
                    return int(cl)
        except Exception:
            pass
        return None

    def _download_single_file(self, filename: str) -> bool:
        """Download or resume a single file using HTTP Range requests."""
        if self.cancel_requested:
            return False

        target_path = MING_MODEL_DIR / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"{HF_BASE_URL}/{filename}"

        existing_size = target_path.stat().st_size if target_path.exists() else 0
        remote_size = self._get_remote_file_size(url)

        # Skip if already fully downloaded
        if remote_size and existing_size >= remote_size:
            with self.lock:
                self.downloaded_bytes += existing_size
            return True

        headers = {
            "User-Agent": "MingStudio/3.0 (MoE Downloader)"
        }
        mode = "wb"
        if existing_size > 0 and remote_size and existing_size < remote_size:
            headers["Range"] = f"bytes={existing_size}-"
            mode = "ab"
            with self.lock:
                self.downloaded_bytes += existing_size

        with self.lock:
            self.current_files[filename] = existing_size

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                chunk_size = 512 * 1024  # 512KB chunks
                with open(target_path, mode) as f:
                    while not self.cancel_requested:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        chunk_len = len(chunk)
                        now = time.time()

                        with self.lock:
                            self.downloaded_bytes += chunk_len
                            self.current_files[filename] = self.current_files.get(filename, 0) + chunk_len
                            self.speed_history.append((now, chunk_len))

                            # Clean up old history (> 3 seconds)
                            cutoff = now - 3.0
                            self.speed_history = [item for item in self.speed_history if item[0] >= cutoff]

                            # Calculate current speed
                            if self.speed_history:
                                total_recent_bytes = sum(item[1] for item in self.speed_history)
                                time_span = max(0.2, now - self.speed_history[0][0])
                                speed_bytes_per_sec = total_recent_bytes / time_span
                                self.current_speed_mbps = speed_bytes_per_sec / (1024 * 1024)

                                remaining = max(0, self.total_bytes - self.downloaded_bytes)
                                if speed_bytes_per_sec > 1024:
                                    self.eta_seconds = int(remaining / speed_bytes_per_sec)
                                else:
                                    self.eta_seconds = 0
            return True
        except Exception as e:
            if not self.cancel_requested:
                self.error_message = f"Download error for {filename}: {str(e)}"
            return False
        finally:
            with self.lock:
                self.current_files.pop(filename, None)

    def _worker_loop(self):
        """Execute parallel download across all 30 safetensors and config files."""
        self.status = "downloading"
        self.is_downloading = True
        self.cancel_requested = False
        self.error_message = ""
        self.speed_history.clear()

        # Build download queue: essential configs first, then 30 safetensors shards
        file_queue = list(ESSENTIAL_CONFIG_FILES) + list(EXPECTED_SAFETENSORS)
        
        # Pre-scan existing bytes on disk
        initial_bytes = 0
        for f in file_queue:
            p = MING_MODEL_DIR / f
            if p.exists():
                initial_bytes += p.stat().st_size
        with self.lock:
            self.downloaded_bytes = initial_bytes

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._download_single_file, fname): fname for fname in file_queue}
                for fut in as_completed(futures):
                    fname = futures[fut]
                    if self.cancel_requested:
                        break
                    try:
                        fut.result()
                    except Exception as ex:
                        self.error_message = f"Worker failed on {fname}: {ex}"

            if self.cancel_requested:
                self.status = "cancelled"
            elif self.error_message:
                self.status = "error"
            else:
                self.status = "completed"
                self.current_speed_mbps = 0.0
                self.eta_seconds = 0
        except Exception as ex:
            self.status = "error"
            self.error_message = str(ex)
        finally:
            self.is_downloading = False

    def start(self) -> bool:
        """Start asynchronous multi-threaded download if not already active."""
        with self.lock:
            if self.is_downloading:
                return False
            self.is_downloading = True
            self.cancel_requested = False
            self.status = "downloading"

        t = threading.Thread(target=self._worker_loop, daemon=True)
        t.start()
        return True

    def cancel(self):
        """Signal background threads to abort immediately."""
        with self.lock:
            self.cancel_requested = True
            self.status = "cancelled"
            self.is_downloading = False


# Global singleton instance
downloader_instance = ModelDownloader(max_workers=8)
