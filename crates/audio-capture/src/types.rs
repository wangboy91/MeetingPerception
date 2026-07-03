use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AudioDevice {
    pub id: String,
    pub name: String,
    pub track: AudioTrack,
    pub is_default: bool,
    pub platform: String,
    pub available: bool,
    pub note: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub enum AudioTrack {
    Mic,
    System,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CaptureConfig {
    pub session_id: String,
    pub mic_device_id: Option<String>,
    pub system_device_id: Option<String>,
    pub enable_mic: bool,
    pub enable_system: bool,
    pub sample_rate: u32,
    pub channels: u16,
    pub frame_duration_ms: u16,
}

impl CaptureConfig {
    pub fn normalized(self) -> Self {
        Self {
            sample_rate: if self.sample_rate == 0 {
                16_000
            } else {
                self.sample_rate
            },
            channels: if self.channels == 0 { 1 } else { self.channels },
            frame_duration_ms: if self.frame_duration_ms == 0 {
                100
            } else {
                self.frame_duration_ms
            },
            ..self
        }
    }
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AudioFrame {
    pub session_id: String,
    pub track: AudioTrack,
    pub timestamp_ms: u64,
    pub sample_rate: u32,
    pub channels: u16,
    pub format: String,
    pub seq: u64,
    pub rms: f32,
    pub data: Vec<i16>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CaptureStatus {
    pub is_running: bool,
    pub mic_active: bool,
    pub system_active: bool,
    pub message: String,
}

pub type AudioFrameSink = Arc<dyn Fn(AudioFrame) + Send + Sync + 'static>;

pub trait AudioCaptureProvider {
    fn list_devices(&self) -> Result<Vec<AudioDevice>, String>;
    fn set_frame_sink(&mut self, sink: Option<AudioFrameSink>);
    fn start(&mut self, config: CaptureConfig) -> Result<CaptureStatus, String>;
    fn stop(&mut self) -> Result<CaptureStatus, String>;
    fn status(&self) -> CaptureStatus;
}
