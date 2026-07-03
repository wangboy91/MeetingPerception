use audio_capture::AudioCaptureProvider;
use std::net::TcpStream;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::{AppHandle, Emitter};

struct AudioCaptureState(Mutex<audio_capture::NativeAudioCaptureProvider>);
struct AiServiceState(Mutex<Option<Child>>);

impl Drop for AiServiceState {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.0.lock() {
            if let Some(mut child) = guard.take() {
                let _ = child.kill();
            }
        }
    }
}

#[tauri::command]
fn list_audio_devices(
    state: tauri::State<'_, AudioCaptureState>,
) -> Result<Vec<audio_capture::AudioDevice>, String> {
    state
        .0
        .lock()
        .map_err(|_| "Audio capture state lock is poisoned.".to_string())?
        .list_devices()
}

#[tauri::command]
fn start_audio_capture(
    app: AppHandle,
    state: tauri::State<'_, AudioCaptureState>,
    config: audio_capture::CaptureConfig,
) -> Result<audio_capture::CaptureStatus, String> {
    let app_for_frames = app.clone();
    let mut provider = state
        .0
        .lock()
        .map_err(|_| "Audio capture state lock is poisoned.".to_string())?;

    provider.set_frame_sink(Some(std::sync::Arc::new(move |frame| {
        if let Err(err) = app_for_frames.emit("audio.frame.native", frame) {
            eprintln!("failed to emit native audio frame: {err}");
        }
    })));
    provider.start(config)
}

#[tauri::command]
fn stop_audio_capture(
    state: tauri::State<'_, AudioCaptureState>,
) -> Result<audio_capture::CaptureStatus, String> {
    state
        .0
        .lock()
        .map_err(|_| "Audio capture state lock is poisoned.".to_string())?
        .stop()
}

#[tauri::command]
fn audio_capture_status(
    state: tauri::State<'_, AudioCaptureState>,
) -> Result<audio_capture::CaptureStatus, String> {
    Ok(state
        .0
        .lock()
        .map_err(|_| "Audio capture state lock is poisoned.".to_string())?
        .status())
}

#[tauri::command]
fn ai_service_status() -> Result<String, String> {
    if TcpStream::connect("127.0.0.1:8765").is_ok() {
        Ok("running".to_string())
    } else {
        Ok("stopped".to_string())
    }
}

fn start_ai_service_if_needed(state: &AiServiceState) {
    if TcpStream::connect("127.0.0.1:8765").is_ok() {
        return;
    }

    let Ok(mut guard) = state.0.lock() else {
        return;
    };
    if guard.is_some() {
        return;
    }

    let repo_root = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("..");
    let service_dir = repo_root.join("services").join("ai-service");
    let child = Command::new("python")
        .args([
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ])
        .current_dir(service_dir)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn();

    match child {
        Ok(child) => {
            *guard = Some(child);
        }
        Err(err) => {
            eprintln!("failed to auto-start AI Service: {err}");
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AudioCaptureState(Mutex::new(
            audio_capture::create_audio_capture_provider(),
        )))
        .manage(AiServiceState(Mutex::new(None)))
        .setup(|app| {
            let state = app.state::<AiServiceState>();
            start_ai_service_if_needed(state.inner());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            list_audio_devices,
            start_audio_capture,
            stop_audio_capture,
            audio_capture_status,
            ai_service_status
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Meeting Copilot desktop app");
}
