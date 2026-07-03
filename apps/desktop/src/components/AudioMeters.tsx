import { AudioLevel } from "@meeting-copilot/shared";

interface AudioMetersProps {
  localMicLevel: number;
  serverMicLevel?: AudioLevel;
  serverSystemLevel?: AudioLevel;
  micError?: string | null;
}

export function AudioMeters({
  localMicLevel,
  serverMicLevel,
  serverSystemLevel,
  micError,
}: AudioMetersProps) {
  const micLevel = serverMicLevel?.level ?? localMicLevel;
  const systemLevel = serverSystemLevel?.level ?? 0;

  return (
    <section className="audio-meters" aria-label="音频输入状态">
      <Meter
        label="Mic"
        level={micLevel}
        note={micError ?? (serverMicLevel?.isSpeech ? "检测到语音" : "监听中")}
      />
      <Meter
        label="System"
        level={systemLevel}
        note={serverSystemLevel?.isSpeech ? "检测到系统输出语音" : "Windows loopback 监听中"}
      />
    </section>
  );
}

function Meter({ label, level, note }: { label: string; level: number; note: string }) {
  const percent = Math.min(100, Math.round(level * 100));
  return (
    <div className="audio-meter-row">
      <div>
        <strong>{label}</strong>
        <small>{note}</small>
      </div>
      <div className="level-bar" aria-label={`${label} 音量 ${percent}%`}>
        <span style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
