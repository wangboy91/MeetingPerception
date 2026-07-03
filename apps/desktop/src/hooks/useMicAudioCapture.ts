import { AudioFramePayload } from "@meeting-copilot/shared";
import { useEffect, useRef, useState } from "react";

const TARGET_SAMPLE_RATE = 16000;

type SendAudioFrame = (payload: AudioFramePayload) => void;

export function useMicAudioCapture(
  sessionId: string,
  enabled: boolean,
  deviceId: string,
  sendAudioFrame: SendAudioFrame,
) {
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const seqRef = useRef(0);
  const startedAtRef = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;
    let stream: MediaStream | null = null;
    let audioContext: AudioContext | null = null;
    let source: MediaStreamAudioSourceNode | null = null;
    let processor: ScriptProcessorNode | null = null;
    seqRef.current = 0;
    startedAtRef.current = performance.now();

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            deviceId: deviceId === "default" ? undefined : { exact: deviceId },
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        audioContext = new AudioContext();
        source = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(2048, 1, 1);

        processor.onaudioprocess = (event) => {
          const input = event.inputBuffer.getChannelData(0);
          const pcm = downsampleTo16BitPcm(input, audioContext?.sampleRate ?? TARGET_SAMPLE_RATE);
          const rms = calculateRms(pcm);

          setLevel(rms);
          sendAudioFrame({
            sessionId,
            track: "mic",
            timestampMs: Math.round(performance.now() - (startedAtRef.current ?? performance.now())),
            sampleRate: TARGET_SAMPLE_RATE,
            channels: 1,
            format: "pcm_s16le",
            seq: seqRef.current,
            rms,
            data: int16ToBase64(pcm),
          });
          seqRef.current += 1;
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
        setError(null);
      } catch {
        setError("无法访问麦克风，请检查系统权限或浏览器授权");
      }
    }

    void start();

    return () => {
      cancelled = true;
      processor?.disconnect();
      source?.disconnect();
      stream?.getTracks().forEach((track) => track.stop());
      void audioContext?.close();
    };
  }, [deviceId, enabled, sendAudioFrame, sessionId]);

  return { level, error };
}

function downsampleTo16BitPcm(input: Float32Array, inputSampleRate: number): Int16Array {
  if (inputSampleRate === TARGET_SAMPLE_RATE) {
    return floatTo16BitPcm(input);
  }

  const ratio = inputSampleRate / TARGET_SAMPLE_RATE;
  const outputLength = Math.max(1, Math.floor(input.length / ratio));
  const output = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i += 1) {
    const start = Math.floor(i * ratio);
    const end = Math.min(input.length, Math.floor((i + 1) * ratio));
    let sum = 0;
    for (let j = start; j < end; j += 1) {
      sum += input[j] ?? 0;
    }
    output[i] = sum / Math.max(1, end - start);
  }

  return floatTo16BitPcm(output);
}

function floatTo16BitPcm(input: Float32Array): Int16Array {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, input[i] ?? 0));
    output[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return output;
}

function calculateRms(pcm: Int16Array): number {
  if (pcm.length === 0) {
    return 0;
  }

  let sum = 0;
  for (const sample of pcm) {
    const normalized = sample / 32768;
    sum += normalized * normalized;
  }
  return Math.min(1, Math.sqrt(sum / pcm.length));
}

function int16ToBase64(pcm: Int16Array): string {
  const bytes = new Uint8Array(pcm.buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i] ?? 0);
  }
  return btoa(binary);
}
