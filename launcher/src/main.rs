#![windows_subsystem = "windows"]

use std::env;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};

const CREATE_NO_WINDOW: u32 = 0x08000000;

#[link(name = "user32")]
extern "system" {
    fn MessageBoxW(
        hwnd: *mut std::ffi::c_void,
        text: *const u16,
        caption: *const u16,
        utype: u32,
    ) -> i32;
}

fn show_info_box(title: &str, message: &str) {
    let title_utf16: Vec<u16> = title.encode_utf16().chain(std::iter::once(0)).collect();
    let message_utf16: Vec<u16> = message.encode_utf16().chain(std::iter::once(0)).collect();
    unsafe {
        // MB_OK (0) | MB_ICONINFORMATION (0x40)
        MessageBoxW(
            std::ptr::null_mut(),
            message_utf16.as_ptr(),
            title_utf16.as_ptr(),
            0x00000040,
        );
    }
}

fn log_message(log_path: &Path, message: &str) {
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
        let _ = writeln!(file, "[MingStudio] {}", message);
    }
}

fn detect_hardware() -> (String, bool, u64) {
    let mut cmd = Command::new("nvidia-smi");
    cmd.args(["--query-gpu=name,memory.total", "--format=csv,noheader"]);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }

    if let Ok(output) = cmd.output() {
        if output.status.success() {
            let text = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !text.is_empty() {
                let parts: Vec<&str> = text.split(',').map(|s| s.trim()).collect();
                let name = parts.first().unwrap_or(&"NVIDIA GPU").to_string();
                let vram = parts.get(1).and_then(|v| {
                    v.split_whitespace().next().and_then(|num| num.parse::<u64>().ok())
                }).unwrap_or(0);
                return (name, true, vram);
            }
        }
    }

    ("Standard CPU Graphics".to_string(), false, 0)
}

fn main() {
    let current_exe = match env::current_exe() {
        Ok(p) => p,
        Err(_) => return,
    };

    let portable_root = match current_exe.parent() {
        Some(p) => p.to_path_buf(),
        None => return,
    };

    let data_dir = portable_root.join("data");
    let models_dir = data_dir.join("models");
    let voices_dir = data_dir.join("voices");
    let outputs_dir = data_dir.join("outputs");
    let logs_dir = portable_root.join("logs");

    for d in &[&data_dir, &models_dir, &voices_dir, &outputs_dir, &logs_dir] {
        let _ = fs::create_dir_all(d);
    }

    let log_file = logs_dir.join("launcher.log");
    log_message(&log_file, "MingStudio Universal AI Voice Workstation Launcher Started");

    let (gpu_name, is_nvidia, vram_mb) = detect_hardware();
    log_message(&log_file, &format!("Hardware Detected: {} (VRAM: {} MB, CUDA: {})", gpu_name, vram_mb, is_nvidia));

    // Launch Frontend via default webview or browser app window
    let frontend_index = portable_root.join("frontend").join("index.html");
    if frontend_index.exists() {
        let url = format!("file:///{}", frontend_index.display().to_string().replace('\\', "/"));
        
        // Try launching Edge in App mode for a native window feel:
        // msedge.exe --app=file:///...
        let app_launched = Command::new("msedge.exe")
            .arg(format!("--app={}", url))
            .arg("--window-size=1280,840")
            .spawn()
            .is_ok();

        if !app_launched {
            // Fallback to default browser
            let _ = Command::new("cmd")
                .args(["/c", "start", "", &url])
                .spawn();
        }
    } else {
        show_info_box("MingStudio 오류", "frontend/index.html 파일을 찾을 수 없습니다.");
    }
}
