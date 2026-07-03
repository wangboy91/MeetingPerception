use crate::platform::{current_platform, system_output_placeholder};
use crate::types::{
    AudioCaptureProvider, AudioDevice, AudioFrame, AudioFrameSink, AudioTrack, CaptureConfig,
    CaptureStatus,
};
#[cfg(windows)]
use crate::windows_loopback::WindowsLoopbackCapture;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Sample, SampleFormat, SizedSample, Stream};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

pub struct NativeAudioCaptureProvider {
    frame_sink: Option<AudioFrameSink>,
    mic_stream: Option<Stream>,
    #[cfg(windows)]
    system_capture: Option<WindowsLoopbackCapture>,
    started_at: Option<Instant>,
    status: CaptureStatus,
}

impl NativeAudioCaptureProvider {
    pub fn new() -> Self {
        Self {
            frame_sink: None,
            mic_stream: None,
            #[cfg(windows)]
            system_capture: None,
            started_at: None,
            status: CaptureStatus {
                is_running: false,
                mic_active: false,
                system_active: false,
                message: "Audio capture is idle.".to_string(),
            },
        }
    }

    fn start_mic(&mut self, config: &CaptureConfig) -> Result<(), String> {
        let host = cpal::default_host();
        let device = select_input_device(&host, config.mic_device_id.as_deref())?;
        let input_config = device
            .default_input_config()
            .map_err(|err| format!("Failed to read microphone config: {err}"))?;
        let sample_format = input_config.sample_format();
        let stream_config = input_config.config();
        let source_sample_rate = stream_config.sample_rate.0;
        let source_channels = stream_config.channels;
        let target_sample_rate = config.sample_rate;
        let frame_samples =
            ((target_sample_rate as u64 * config.frame_duration_ms as u64) / 1000).max(1) as usize;
        let session_id = config.session_id.clone();
        let sink = self.frame_sink.clone();
        let started_at = self.started_at.unwrap_or_else(Instant::now);
        let seq = Arc::new(Mutex::new(0_u64));
        let pcm_buffer = Arc::new(Mutex::new(Vec::<i16>::with_capacity(frame_samples * 2)));

        let err_fn = |err| {
            eprintln!("audio capture stream error: {err}");
        };

        let stream = match sample_format {
            SampleFormat::F32 => build_input_stream::<f32>(
                &device,
                &stream_config,
                MicStreamContext {
                    session_id,
                    source_sample_rate,
                    source_channels,
                    target_sample_rate,
                    frame_samples,
                    started_at,
                    seq,
                    pcm_buffer,
                    sink,
                },
                err_fn,
            ),
            SampleFormat::I16 => build_input_stream::<i16>(
                &device,
                &stream_config,
                MicStreamContext {
                    session_id,
                    source_sample_rate,
                    source_channels,
                    target_sample_rate,
                    frame_samples,
                    started_at,
                    seq,
                    pcm_buffer,
                    sink,
                },
                err_fn,
            ),
            SampleFormat::U16 => build_input_stream::<u16>(
                &device,
                &stream_config,
                MicStreamContext {
                    session_id,
                    source_sample_rate,
                    source_channels,
                    target_sample_rate,
                    frame_samples,
                    started_at,
                    seq,
                    pcm_buffer,
                    sink,
                },
                err_fn,
            ),
            other => Err(format!("Unsupported microphone sample format: {other:?}")),
        }?;

        stream
            .play()
            .map_err(|err| format!("Failed to start microphone stream: {err}"))?;
        self.mic_stream = Some(stream);
        Ok(())
    }

    #[cfg(windows)]
    fn start_system(&mut self, config: &CaptureConfig) -> Result<(), String> {
        let capture = WindowsLoopbackCapture::start(config.clone(), self.frame_sink.clone())?;
        self.system_capture = Some(capture);
        Ok(())
    }

    #[cfg(not(windows))]
    fn start_system(&mut self, _config: &CaptureConfig) -> Result<(), String> {
        Err(crate::platform::system_capture_status())
    }
}

impl Default for NativeAudioCaptureProvider {
    fn default() -> Self {
        Self::new()
    }
}

impl AudioCaptureProvider for NativeAudioCaptureProvider {
    fn list_devices(&self) -> Result<Vec<AudioDevice>, String> {
        let host = cpal::default_host();
        let default_name = host
            .default_input_device()
            .and_then(|device| device.name().ok());
        let mut devices = Vec::new();

        if let Ok(input_devices) = host.input_devices() {
            for (index, device) in input_devices.enumerate() {
                let name = device
                    .name()
                    .unwrap_or_else(|_| format!("Microphone {}", index + 1));
                let is_default = default_name.as_ref() == Some(&name);
                devices.push(AudioDevice {
                    id: mic_device_id(index, &name),
                    name,
                    track: AudioTrack::Mic,
                    is_default,
                    platform: current_platform(),
                    available: true,
                    note: None,
                });
            }
        }

        if devices.is_empty() {
            devices.push(AudioDevice {
                id: "default-mic".to_string(),
                name: "Default Microphone".to_string(),
                track: AudioTrack::Mic,
                is_default: true,
                platform: current_platform(),
                available: false,
                note: Some("No microphone devices were reported by the native host.".to_string()),
            });
        }

        devices.push(system_output_placeholder());
        Ok(devices)
    }

    fn set_frame_sink(&mut self, sink: Option<AudioFrameSink>) {
        self.frame_sink = sink;
    }

    fn start(&mut self, config: CaptureConfig) -> Result<CaptureStatus, String> {
        let config = config.normalized();
        self.stop()?;
        self.started_at = Some(Instant::now());

        if config.enable_mic {
            self.start_mic(&config)?;
        }

        if config.enable_system {
            self.start_system(&config)?;
            self.status.message = "Mic and system output capture started.".to_string();
        } else {
            self.status.message = "Mic capture started.".to_string();
        }

        let system_active = self.is_system_active();
        self.status.is_running = self.mic_stream.is_some() || system_active;
        self.status.mic_active = self.mic_stream.is_some();
        self.status.system_active = system_active;
        Ok(self.status())
    }

    fn stop(&mut self) -> Result<CaptureStatus, String> {
        self.mic_stream = None;
        #[cfg(windows)]
        if let Some(mut capture) = self.system_capture.take() {
            capture.stop();
        }
        self.started_at = None;
        self.status = CaptureStatus {
            is_running: false,
            mic_active: false,
            system_active: false,
            message: "Audio capture stopped.".to_string(),
        };
        Ok(self.status())
    }

    fn status(&self) -> CaptureStatus {
        self.status.clone()
    }
}

impl NativeAudioCaptureProvider {
    #[cfg(windows)]
    fn is_system_active(&self) -> bool {
        self.system_capture.is_some()
    }

    #[cfg(not(windows))]
    fn is_system_active(&self) -> bool {
        false
    }
}

struct MicStreamContext {
    session_id: String,
    source_sample_rate: u32,
    source_channels: u16,
    target_sample_rate: u32,
    frame_samples: usize,
    started_at: Instant,
    seq: Arc<Mutex<u64>>,
    pcm_buffer: Arc<Mutex<Vec<i16>>>,
    sink: Option<AudioFrameSink>,
}

fn build_input_stream<T>(
    device: &cpal::Device,
    config: &cpal::StreamConfig,
    ctx: MicStreamContext,
    err_fn: impl FnMut(cpal::StreamError) + Send + 'static,
) -> Result<Stream, String>
where
    T: Sample + SizedSample + Send + 'static,
    f32: cpal::FromSample<T>,
{
    device
        .build_input_stream(
            config,
            move |data: &[T], _| {
                let mono = interleaved_to_mono(data, ctx.source_channels);
                let pcm = resample_to_i16(&mono, ctx.source_sample_rate, ctx.target_sample_rate);
                emit_frames(&ctx, &pcm);
            },
            err_fn,
            None,
        )
        .map_err(|err| format!("Failed to build microphone stream: {err}"))
}

fn select_input_device(
    host: &cpal::Host,
    requested_id: Option<&str>,
) -> Result<cpal::Device, String> {
    if requested_id.is_none() || requested_id == Some("default") {
        return host
            .default_input_device()
            .ok_or_else(|| "No default microphone device found.".to_string());
    }

    let requested_id = requested_id.unwrap_or_default();
    let devices = host
        .input_devices()
        .map_err(|err| format!("Failed to enumerate microphone devices: {err}"))?;

    for (index, device) in devices.enumerate() {
        let name = device
            .name()
            .unwrap_or_else(|_| format!("Microphone {}", index + 1));
        if mic_device_id(index, &name) == requested_id || name == requested_id {
            return Ok(device);
        }
    }

    Err(format!("Microphone device not found: {requested_id}"))
}

fn mic_device_id(index: usize, name: &str) -> String {
    format!("mic:{index}:{name}")
}

fn interleaved_to_mono<T>(data: &[T], channels: u16) -> Vec<f32>
where
    T: Sample,
    f32: cpal::FromSample<T>,
{
    let channels = usize::from(channels.max(1));
    data.chunks(channels)
        .map(|frame| {
            let sum: f32 = frame.iter().map(|sample| sample.to_sample::<f32>()).sum();
            sum / channels as f32
        })
        .collect()
}

fn resample_to_i16(input: &[f32], source_rate: u32, target_rate: u32) -> Vec<i16> {
    if input.is_empty() {
        return Vec::new();
    }

    if source_rate == target_rate {
        return input.iter().map(|sample| f32_to_i16(*sample)).collect();
    }

    let ratio = source_rate as f64 / target_rate as f64;
    let output_len = ((input.len() as f64) / ratio).floor().max(1.0) as usize;
    let mut output = Vec::with_capacity(output_len);

    for i in 0..output_len {
        let src_index = ((i as f64) * ratio).floor() as usize;
        output.push(f32_to_i16(input[src_index.min(input.len() - 1)]));
    }

    output
}

fn emit_frames(ctx: &MicStreamContext, pcm: &[i16]) {
    let Some(sink) = ctx.sink.as_ref() else {
        return;
    };

    let Ok(mut buffer) = ctx.pcm_buffer.lock() else {
        return;
    };

    buffer.extend_from_slice(pcm);
    while buffer.len() >= ctx.frame_samples {
        let frame_data: Vec<i16> = buffer.drain(..ctx.frame_samples).collect();
        let Ok(mut seq_guard) = ctx.seq.lock() else {
            return;
        };
        let seq = *seq_guard;
        *seq_guard += 1;
        drop(seq_guard);

        let timestamp_ms = elapsed_ms(ctx.started_at);
        let rms = calculate_rms(&frame_data);
        sink(AudioFrame {
            session_id: ctx.session_id.clone(),
            track: AudioTrack::Mic,
            timestamp_ms,
            sample_rate: ctx.target_sample_rate,
            channels: 1,
            format: "pcm_s16le".to_string(),
            seq,
            rms,
            data: frame_data,
        });
    }
}

fn elapsed_ms(started_at: Instant) -> u64 {
    let elapsed = Instant::now()
        .checked_duration_since(started_at)
        .unwrap_or_else(|| Duration::from_millis(0));
    elapsed.as_millis() as u64
}

fn calculate_rms(samples: &[i16]) -> f32 {
    if samples.is_empty() {
        return 0.0;
    }

    let sum: f32 = samples
        .iter()
        .map(|sample| {
            let normalized = *sample as f32 / 32768.0;
            normalized * normalized
        })
        .sum();
    (sum / samples.len() as f32).sqrt().min(1.0)
}

fn f32_to_i16(sample: f32) -> i16 {
    let clamped = sample.clamp(-1.0, 1.0);
    if clamped < 0.0 {
        (clamped * 32768.0) as i16
    } else {
        (clamped * 32767.0) as i16
    }
}
