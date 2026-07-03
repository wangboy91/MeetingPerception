use crate::types::{AudioFrame, AudioFrameSink, AudioTrack, CaptureConfig};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};
use windows::core::Interface;
use windows::Win32::Media::Audio::{
    eConsole, eRender, IAudioCaptureClient, IAudioClient, IMMDeviceEnumerator, MMDeviceEnumerator,
    AUDCLNT_SHAREMODE_SHARED, AUDCLNT_STREAMFLAGS_LOOPBACK, WAVEFORMATEX,
};
use windows::Win32::Media::KernelStreaming::{
    KSDATAFORMAT_SUBTYPE_IEEE_FLOAT, KSDATAFORMAT_SUBTYPE_PCM,
};
use windows::Win32::System::Com::{
    CoCreateInstance, CoInitializeEx, CoTaskMemFree, CoUninitialize, CLSCTX_ALL,
    COINIT_MULTITHREADED, STGM_READ,
};

const WAVE_FORMAT_PCM: u16 = 0x0001;
const WAVE_FORMAT_IEEE_FLOAT: u16 = 0x0003;
const WAVE_FORMAT_EXTENSIBLE: u16 = 0xFFFE;
const REFTIMES_PER_SEC: i64 = 10_000_000;

pub struct WindowsLoopbackCapture {
    stop_flag: Arc<AtomicBool>,
    thread: Option<JoinHandle<()>>,
}

impl WindowsLoopbackCapture {
    pub fn start(config: CaptureConfig, sink: Option<AudioFrameSink>) -> Result<Self, String> {
        let stop_flag = Arc::new(AtomicBool::new(false));
        let thread_stop = Arc::clone(&stop_flag);
        let builder = thread::Builder::new().name("meeting-copilot-wasapi-loopback".to_string());
        let thread = builder
            .spawn(move || {
                if let Err(err) = capture_loop(config, sink, thread_stop) {
                    eprintln!("wasapi loopback capture stopped: {err}");
                }
            })
            .map_err(|err| format!("Failed to start WASAPI loopback thread: {err}"))?;

        Ok(Self {
            stop_flag,
            thread: Some(thread),
        })
    }

    pub fn stop(&mut self) {
        self.stop_flag.store(true, Ordering::SeqCst);
        if let Some(thread) = self.thread.take() {
            let _ = thread.join();
        }
    }
}

impl Drop for WindowsLoopbackCapture {
    fn drop(&mut self) {
        self.stop();
    }
}

fn capture_loop(
    config: CaptureConfig,
    sink: Option<AudioFrameSink>,
    stop_flag: Arc<AtomicBool>,
) -> Result<(), String> {
    unsafe {
        CoInitializeEx(None, COINIT_MULTITHREADED)
            .map_err(|err| format!("Failed to initialize COM for WASAPI loopback: {err}"))?;
    }
    let result = run_wasapi_loop(config, sink, stop_flag);
    unsafe {
        CoUninitialize();
    }
    result
}

fn run_wasapi_loop(
    config: CaptureConfig,
    sink: Option<AudioFrameSink>,
    stop_flag: Arc<AtomicBool>,
) -> Result<(), String> {
    let enumerator: IMMDeviceEnumerator = unsafe {
        CoCreateInstance(&MMDeviceEnumerator, None, CLSCTX_ALL)
            .map_err(|err| format!("Failed to create WASAPI device enumerator: {err}"))?
    };
    let device = unsafe {
        enumerator
            .GetDefaultAudioEndpoint(eRender, eConsole)
            .map_err(|err| format!("Failed to get default render endpoint: {err}"))?
    };
    let audio_client: IAudioClient = unsafe {
        device
            .Activate(CLSCTX_ALL, None)
            .map_err(|err| format!("Failed to activate WASAPI audio client: {err}"))?
    };
    let mix_format = unsafe {
        audio_client
            .GetMixFormat()
            .map_err(|err| format!("Failed to read WASAPI mix format: {err}"))?
    };
    let format = unsafe { *mix_format };
    let buffer_duration = REFTIMES_PER_SEC;
    unsafe {
        audio_client
            .Initialize(
                AUDCLNT_SHAREMODE_SHARED,
                AUDCLNT_STREAMFLAGS_LOOPBACK,
                buffer_duration,
                0,
                mix_format,
                None,
            )
            .map_err(|err| format!("Failed to initialize WASAPI loopback client: {err}"))?;
    }
    unsafe {
        CoTaskMemFree(Some(mix_format.cast()));
    }

    let capture_client: IAudioCaptureClient = unsafe {
        audio_client
            .GetService()
            .map_err(|err| format!("Failed to get WASAPI capture client: {err}"))?
    };
    unsafe {
        audio_client
            .Start()
            .map_err(|err| format!("Failed to start WASAPI loopback client: {err}"))?;
    }

    let result = read_packets(&config, &format, &capture_client, sink, stop_flag);
    unsafe {
        let _ = audio_client.Stop();
    }
    result
}

fn read_packets(
    config: &CaptureConfig,
    format: &WAVEFORMATEX,
    capture_client: &IAudioCaptureClient,
    sink: Option<AudioFrameSink>,
    stop_flag: Arc<AtomicBool>,
) -> Result<(), String> {
    let started_at = Instant::now();
    let frame_samples =
        ((config.sample_rate as u64 * config.frame_duration_ms as u64) / 1000).max(1) as usize;
    let ctx = LoopbackContext {
        session_id: config.session_id.clone(),
        source_sample_rate: format.nSamplesPerSec,
        source_channels: format.nChannels,
        target_sample_rate: config.sample_rate,
        frame_samples,
        started_at,
        seq: Arc::new(Mutex::new(0)),
        pcm_buffer: Arc::new(Mutex::new(Vec::with_capacity(frame_samples * 2))),
        sink,
    };

    while !stop_flag.load(Ordering::SeqCst) {
        let mut packet_frames = 0_u32;
        unsafe {
            capture_client
                .GetNextPacketSize(&mut packet_frames)
                .map_err(|err| format!("Failed to read WASAPI packet size: {err}"))?;
        }
        if packet_frames == 0 {
            thread::sleep(Duration::from_millis(10));
            continue;
        }

        let mut data = std::ptr::null_mut();
        let mut frames_available = 0_u32;
        let mut flags = 0_u32;
        unsafe {
            capture_client
                .GetBuffer(
                    &mut data,
                    &mut frames_available,
                    &mut flags,
                    std::ptr::null_mut(),
                    std::ptr::null_mut(),
                )
                .map_err(|err| format!("Failed to get WASAPI loopback buffer: {err}"))?;
        }

        if !data.is_null() && frames_available > 0 {
            let mono = unsafe { buffer_to_mono(data, frames_available, format)? };
            let pcm = resample_to_i16(&mono, format.nSamplesPerSec, config.sample_rate);
            emit_frames(&ctx, &pcm);
        }

        unsafe {
            capture_client
                .ReleaseBuffer(frames_available)
                .map_err(|err| format!("Failed to release WASAPI loopback buffer: {err}"))?;
        }
    }

    Ok(())
}

struct LoopbackContext {
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

unsafe fn buffer_to_mono(
    data: *mut u8,
    frames_available: u32,
    format: &WAVEFORMATEX,
) -> Result<Vec<f32>, String> {
    let channels = usize::from(format.nChannels.max(1));
    let frames = frames_available as usize;
    let sample_count = frames * channels;
    let bits = format.wBitsPerSample;

    if format.wFormatTag == WAVE_FORMAT_IEEE_FLOAT || is_extensible_float(format) {
        let samples = std::slice::from_raw_parts(data.cast::<f32>(), sample_count);
        return Ok(interleaved_f32_to_mono(samples, channels));
    }

    if format.wFormatTag == WAVE_FORMAT_PCM || is_extensible_pcm(format) {
        if bits == 16 {
            let samples = std::slice::from_raw_parts(data.cast::<i16>(), sample_count);
            return Ok(interleaved_i16_to_mono(samples, channels));
        }
        if bits == 32 {
            let samples = std::slice::from_raw_parts(data.cast::<i32>(), sample_count);
            return Ok(interleaved_i32_to_mono(samples, channels));
        }
    }

    Err(format!(
        "Unsupported WASAPI loopback format: tag={} bits={}",
        format.wFormatTag, bits
    ))
}

fn is_extensible_float(format: &WAVEFORMATEX) -> bool {
    format.wFormatTag == WAVE_FORMAT_EXTENSIBLE
        && unsafe {
            let extensible = (format as *const WAVEFORMATEX)
                .cast::<windows::Win32::Media::Audio::WAVEFORMATEXTENSIBLE>();
            (*extensible).SubFormat == KSDATAFORMAT_SUBTYPE_IEEE_FLOAT
        }
}

fn is_extensible_pcm(format: &WAVEFORMATEX) -> bool {
    format.wFormatTag == WAVE_FORMAT_EXTENSIBLE
        && unsafe {
            let extensible = (format as *const WAVEFORMATEX)
                .cast::<windows::Win32::Media::Audio::WAVEFORMATEXTENSIBLE>();
            (*extensible).SubFormat == KSDATAFORMAT_SUBTYPE_PCM
        }
}

fn interleaved_f32_to_mono(samples: &[f32], channels: usize) -> Vec<f32> {
    samples
        .chunks(channels)
        .map(|frame| frame.iter().copied().sum::<f32>() / channels as f32)
        .collect()
}

fn interleaved_i16_to_mono(samples: &[i16], channels: usize) -> Vec<f32> {
    samples
        .chunks(channels)
        .map(|frame| {
            frame
                .iter()
                .map(|sample| *sample as f32 / 32768.0)
                .sum::<f32>()
                / channels as f32
        })
        .collect()
}

fn interleaved_i32_to_mono(samples: &[i32], channels: usize) -> Vec<f32> {
    samples
        .chunks(channels)
        .map(|frame| {
            frame
                .iter()
                .map(|sample| *sample as f32 / 2_147_483_648.0)
                .sum::<f32>()
                / channels as f32
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

fn emit_frames(ctx: &LoopbackContext, pcm: &[i16]) {
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

        sink(AudioFrame {
            session_id: ctx.session_id.clone(),
            track: AudioTrack::System,
            timestamp_ms: elapsed_ms(ctx.started_at),
            sample_rate: ctx.target_sample_rate,
            channels: 1,
            format: "pcm_s16le".to_string(),
            seq,
            rms: calculate_rms(&frame_data),
            data: frame_data,
        });
    }
}

fn elapsed_ms(started_at: Instant) -> u64 {
    Instant::now()
        .checked_duration_since(started_at)
        .unwrap_or_else(|| Duration::from_millis(0))
        .as_millis() as u64
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
