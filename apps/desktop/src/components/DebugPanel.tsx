import { AudioLevel, MeetingStatus } from "@meeting-copilot/shared";

interface DebugPanelProps {
  status: MeetingStatus;
  audioLevels: Partial<Record<AudioLevel["track"], AudioLevel>>;
  transcriptCount: number;
  suggestionCount: number;
  error?: string | null;
}

export function DebugPanel({
  status,
  audioLevels,
  transcriptCount,
  suggestionCount,
  error,
}: DebugPanelProps) {
  const mic = audioLevels.mic;
  const system = audioLevels.system;
  const totalFrames = (mic?.framesReceived ?? 0) + (system?.framesReceived ?? 0);

  return (
    <section className="debug-panel">
      <div className="debug-item">
        <span>WebSocket</span>
        <strong>{status}</strong>
      </div>
      <div className="debug-item">
        <span>Audio frames</span>
        <strong>{totalFrames}</strong>
      </div>
      <div className="debug-item">
        <span>VAD</span>
        <strong>{mic?.isSpeech || system?.isSpeech ? "speech" : "silence"}</strong>
      </div>
      <div className="debug-item">
        <span>ASR</span>
        <strong>{transcriptCount} transcripts</strong>
      </div>
      <div className="debug-item">
        <span>LLM</span>
        <strong>{suggestionCount} suggestions</strong>
      </div>
      <div className="debug-item debug-error">
        <span>Last error</span>
        <strong>{error ?? "none"}</strong>
      </div>
    </section>
  );
}
