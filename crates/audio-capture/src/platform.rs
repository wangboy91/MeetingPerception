use crate::types::{AudioDevice, AudioTrack};

pub fn current_platform() -> String {
    std::env::consts::OS.to_string()
}

pub fn system_capture_status() -> String {
    match std::env::consts::OS {
        "windows" => "Windows WASAPI loopback provider is available.".to_string(),
        "macos" => {
            "macOS system capture requires ScreenCaptureKit or a virtual audio device.".to_string()
        }
        "linux" => "Linux system capture requires PipeWire/PulseAudio monitor support.".to_string(),
        other => format!("System output capture is not implemented for {other}."),
    }
}

pub fn system_output_placeholder() -> AudioDevice {
    let is_windows = std::env::consts::OS == "windows";
    AudioDevice {
        id: "default-system-output".to_string(),
        name: "Default System Output".to_string(),
        track: AudioTrack::System,
        is_default: true,
        platform: current_platform(),
        available: is_windows,
        note: Some(system_capture_status()),
    }
}
