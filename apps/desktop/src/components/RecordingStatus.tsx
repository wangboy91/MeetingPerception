import { MeetingStatus } from "@meeting-copilot/shared";

interface RecordingStatusProps {
  status: MeetingStatus;
  error?: string | null;
}

export function RecordingStatus({ status, error }: RecordingStatusProps) {
  const label = error ? "连接异常" : status === "recording" ? "录音中" : "连接中";

  return (
    <div className={`recording-status recording-status-${error ? "error" : status}`}>
      <span aria-hidden="true" />
      <strong>{label}</strong>
      <small>{error ?? "Mic 采集中；System loopback 待接入"}</small>
    </div>
  );
}
