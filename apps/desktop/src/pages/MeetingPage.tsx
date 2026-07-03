import {
  AssistantRole,
  MeetingStatus,
  Suggestion,
  TranscriptSegment,
} from "@meeting-copilot/shared";

import { AudioMeters } from "../components/AudioMeters";
import { DebugPanel } from "../components/DebugPanel";
import { MeetingControls } from "../components/MeetingControls";
import { RecordingStatus } from "../components/RecordingStatus";
import { RoleSelector } from "../components/RoleSelector";
import { SuggestionPanel } from "../components/SuggestionPanel";
import { TranscriptTimeline } from "../components/TranscriptTimeline";
import { useMicAudioCapture } from "../hooks/useMicAudioCapture";
import { useMeetingSession } from "../hooks/useMeetingSession";
import { useNativeAudioCapture } from "../hooks/useNativeAudioCapture";
import { stopMeeting } from "../services/aiServiceClient";

interface MeetingPageProps {
  sessionId: string;
  assistantRole: AssistantRole;
  micDeviceId: string;
  onRoleChange: (role: AssistantRole) => void;
  onEnd: () => void;
}

export function MeetingPage({
  sessionId,
  assistantRole,
  micDeviceId,
  onRoleChange,
  onEnd,
}: MeetingPageProps) {
  const { status, transcripts, suggestions, audioLevels, connectionError, sendAudioFrame } =
    useMeetingSession(sessionId);
  const nativeCapture = useNativeAudioCapture(
    sessionId,
    status === "recording",
    micDeviceId,
    sendAudioFrame,
  );
  const { level: localMicLevel, error: micError } = useMicAudioCapture(
    sessionId,
    status === "recording" && nativeCapture.shouldUseBrowserFallback,
    micDeviceId,
    sendAudioFrame,
  );
  const captureError = nativeCapture.error ?? micError;
  const captureLevel = nativeCapture.shouldUseBrowserFallback ? localMicLevel : nativeCapture.level;

  async function handleEnd() {
    try {
      await stopMeeting(sessionId);
    } finally {
      onEnd();
    }
  }

  return (
    <main className="meeting-shell">
      <header className="meeting-header">
        <div>
          <p className="eyebrow">Session {sessionId.slice(0, 8)}</p>
          <h1>会议进行中</h1>
        </div>
        <div className="meeting-header-actions">
          <RoleSelector value={assistantRole} onChange={onRoleChange} />
          <RecordingStatus status={status as MeetingStatus} error={connectionError} />
          <MeetingControls onEnd={handleEnd} />
        </div>
      </header>

      <AudioMeters
        localMicLevel={captureLevel}
        serverMicLevel={audioLevels.mic}
        serverSystemLevel={audioLevels.system}
        micError={captureError}
      />

      <DebugPanel
        status={status as MeetingStatus}
        audioLevels={audioLevels}
        transcriptCount={transcripts.length}
        suggestionCount={suggestions.length}
        error={captureError ?? connectionError}
      />

      <section className="meeting-grid">
        <TranscriptTimeline transcripts={transcripts as TranscriptSegment[]} />
        <SuggestionPanel suggestions={suggestions as Suggestion[]} />
      </section>
    </main>
  );
}
