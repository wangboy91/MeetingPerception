mod native;
mod platform;
mod types;
#[cfg(windows)]
mod windows_loopback;

pub use native::NativeAudioCaptureProvider;
pub use platform::system_capture_status;
pub use types::{
    AudioCaptureProvider, AudioDevice, AudioFrame, AudioFrameSink, AudioTrack, CaptureConfig,
    CaptureStatus,
};

pub fn create_audio_capture_provider() -> NativeAudioCaptureProvider {
    NativeAudioCaptureProvider::new()
}
