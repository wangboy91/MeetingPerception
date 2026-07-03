import { AudioFramePayload } from "@meeting-copilot/shared";
import { invoke } from "@tauri-apps/api/core";
import { listen, UnlistenFn } from "@tauri-apps/api/event";
import { useEffect, useState } from "react";

type SendAudioFrame = (payload: AudioFramePayload) => void;

interface NativeAudioFrame {
  sessionId: string;
  track: "mic" | "system";
  timestampMs: number;
  sampleRate: 16000;
  channels: 1;
  format: "pcm_s16le";
  seq: number;
  rms: number;
  data: number[];
}

interface CaptureStatus {
  isRunning: boolean;
  micActive: boolean;
  systemActive: boolean;
  message: string;
}

export function useNativeAudioCapture(
  sessionId: string,
  enabled: boolean,
  micDeviceId: string,
  sendAudioFrame: SendAudioFrame,
) {
  const [isNativeRuntime] = useState(() => Boolean(window.__TAURI_INTERNALS__));
  const [status, setStatus] = useState<CaptureStatus | null>(null);
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !isNativeRuntime) {
      return;
    }

    let unlisten: UnlistenFn | null = null;
    let cancelled = false;

    async function start() {
      try {
        unlisten = await listen<NativeAudioFrame>("audio.frame.native", (event) => {
          const frame = event.payload;
          setLevel(frame.rms);
          sendAudioFrame({
            sessionId: frame.sessionId,
            track: frame.track,
            timestampMs: frame.timestampMs,
            sampleRate: frame.sampleRate,
            channels: frame.channels,
            format: frame.format,
            seq: frame.seq,
            rms: frame.rms,
            data: int16ArrayToBase64(frame.data),
          });
        });

        const nextStatus = await invoke<CaptureStatus>("start_audio_capture", {
          config: {
            sessionId,
            micDeviceId,
            systemDeviceId: "default-system-output",
            enableMic: true,
            enableSystem: true,
            sampleRate: 16000,
            channels: 1,
            frameDurationMs: 100,
          },
        });

        if (!cancelled) {
          setStatus(nextStatus);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    }

    void start();

    return () => {
      cancelled = true;
      unlisten?.();
      void invoke("stop_audio_capture").catch(() => undefined);
    };
  }, [enabled, isNativeRuntime, micDeviceId, sendAudioFrame, sessionId]);

  return {
    isNativeRuntime,
    shouldUseBrowserFallback: !isNativeRuntime || Boolean(error),
    status,
    level,
    error,
  };
}

function int16ArrayToBase64(samples: number[]): string {
  const pcm = new Int16Array(samples);
  const bytes = new Uint8Array(pcm.buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i] ?? 0);
  }
  return btoa(binary);
}

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}
