import {
  AssistantRole,
  MeetingSession,
  Speaker,
  Suggestion,
  TranscriptSegment,
} from "@meeting-copilot/shared";

const AI_SERVICE_HTTP_URL = "http://127.0.0.1:8765";
const AI_SERVICE_WS_URL = "ws://127.0.0.1:8765";

interface CreateMeetingResponse {
  id: string;
  status: MeetingSession["status"];
  started_at: string;
}

export interface AppSettings {
  asrProvider: "mock" | "funasr";
  diarizationProvider: "mock" | "funasr" | "pyannote";
  llmProvider: "mock" | "openai-compatible" | "anthropic";
  llmBaseUrl: string;
  llmModel: string;
  cloudLlmEnabled: boolean;
  storeTranscript: boolean;
  debugLogTranscript: boolean;
  dataDir: string;
  apiKeyConfigured: boolean;
}

export async function createMeeting(userRole?: AssistantRole): Promise<MeetingSession> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userRole: userRole ?? "tech-review" }),
  });

  if (!response.ok) {
    throw new Error(`AI Service create meeting failed: ${response.status}`);
  }

  const data = (await response.json()) as CreateMeetingResponse;
  return {
    id: data.id,
    status: data.status,
    startedAt: data.started_at,
  };
}

export async function listMeetings(): Promise<MeetingSession[]> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings`);
  if (!response.ok) {
    throw new Error(`AI Service list meetings failed: ${response.status}`);
  }
  const rows = (await response.json()) as Array<{
    id: string;
    title: string;
    mode: string;
    user_role: string;
    status: MeetingSession["status"];
    started_at: string;
    ended_at: string | null;
  }>;
  return rows.map((row) => ({
    id: row.id,
    title: row.title,
    mode: row.mode,
    userRole: row.user_role,
    status: row.status,
    startedAt: row.started_at,
    endedAt: row.ended_at,
  }));
}

export async function deleteMeeting(sessionId: string): Promise<void> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`AI Service delete meeting failed: ${response.status}`);
  }
}

export async function deleteAllMeetings(): Promise<number> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error(`AI Service delete meetings failed: ${response.status}`);
  }
  const data = (await response.json()) as { deleted: number };
  return data.deleted;
}

export async function getSettings(): Promise<AppSettings> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/settings`);
  if (!response.ok) {
    throw new Error(`AI Service get settings failed: ${response.status}`);
  }
  return (await response.json()) as AppSettings;
}

export async function saveSettings(settings: AppSettings): Promise<AppSettings> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!response.ok) {
    throw new Error(`AI Service save settings failed: ${response.status}`);
  }
  return (await response.json()) as AppSettings;
}

export async function stopMeeting(sessionId: string): Promise<void> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}/stop`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`AI Service stop meeting failed: ${response.status}`);
  }
}

export async function getMeeting(sessionId: string): Promise<MeetingSession> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}`);
  if (!response.ok) {
    throw new Error(`AI Service get meeting failed: ${response.status}`);
  }
  const data = (await response.json()) as {
    id: string;
    title: string;
    mode: string;
    user_role: string;
    status: MeetingSession["status"];
    started_at: string;
    ended_at: string | null;
  };
  return {
    id: data.id,
    title: data.title,
    mode: data.mode,
    userRole: data.user_role,
    status: data.status,
    startedAt: data.started_at,
    endedAt: data.ended_at,
  };
}

export async function getTranscripts(sessionId: string): Promise<TranscriptSegment[]> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}/transcripts`);
  if (!response.ok) {
    throw new Error(`AI Service get transcripts failed: ${response.status}`);
  }
  const rows = (await response.json()) as Array<{
    id: string;
    meeting_id: string;
    segment_id: string;
    speaker_label: TranscriptSegment["speaker"];
    display_speaker_label?: TranscriptSegment["speaker"];
    track: TranscriptSegment["track"];
    text: string;
    start_ms: number;
    end_ms: number;
    confidence: number | null;
    is_final: number;
    created_at: string;
  }>;

  return rows.map((row) => ({
    id: row.id,
    sessionId: row.meeting_id,
    segmentId: row.segment_id,
    time: formatDuration(row.end_ms),
    speaker: row.display_speaker_label ?? row.speaker_label,
    track: row.track,
    text: row.text,
    startMs: row.start_ms,
    endMs: row.end_ms,
    confidence: row.confidence ?? undefined,
    isFinal: Boolean(row.is_final),
    createdAt: row.created_at,
  }));
}

export async function getSuggestions(sessionId: string): Promise<Suggestion[]> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}/suggestions`);
  if (!response.ok) {
    throw new Error(`AI Service get suggestions failed: ${response.status}`);
  }
  const rows = (await response.json()) as Array<{
    id: string;
    meeting_id: string;
    priority: Suggestion["priority"];
    title: string;
    problem_essence: string | null;
    risk: string | null;
    suggested_reply: string | null;
    follow_up_question: string | null;
    action_item: string | null;
    created_at: string;
  }>;

  return rows.map((row) => ({
    id: row.id,
    sessionId: row.meeting_id,
    priority: row.priority,
    title: row.title,
    problemEssence: row.problem_essence ?? undefined,
    rationale: row.problem_essence ?? "",
    risk: row.risk ?? undefined,
    recommendedResponse: row.suggested_reply ?? "",
    suggestedReply: row.suggested_reply ?? undefined,
    followUpQuestion: row.follow_up_question ?? undefined,
    actionItem: row.action_item ?? undefined,
    createdAt: row.created_at,
  }));
}

export async function getSpeakers(sessionId: string): Promise<Speaker[]> {
  const response = await fetch(`${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}/speakers`);
  if (!response.ok) {
    throw new Error(`AI Service get speakers failed: ${response.status}`);
  }
  const rows = (await response.json()) as Array<{
    id: string;
    meeting_id: string;
    label: string;
    source: string;
    display_name: string | null;
  }>;
  return rows.map((row) => ({
    id: row.id,
    meetingId: row.meeting_id,
    label: row.label,
    source: row.source,
    displayName: row.display_name,
  }));
}

export async function renameSpeaker(
  sessionId: string,
  speakerId: string,
  displayName: string,
): Promise<Speaker> {
  const response = await fetch(
    `${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}/speakers/${encodeURIComponent(speakerId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ displayName }),
    },
  );
  if (!response.ok) {
    throw new Error(`AI Service rename speaker failed: ${response.status}`);
  }
  const row = (await response.json()) as {
    id: string;
    meeting_id: string;
    label: string;
    source: string;
    display_name: string | null;
  };
  return {
    id: row.id,
    meetingId: row.meeting_id,
    label: row.label,
    source: row.source,
    displayName: row.display_name,
  };
}

export function exportMeetingMarkdownUrl(sessionId: string): string {
  return `${AI_SERVICE_HTTP_URL}/api/meetings/${sessionId}/export?format=markdown`;
}

export function buildMeetingWebSocketUrl(sessionId: string): string {
  return `${AI_SERVICE_WS_URL}/ws/meetings/${sessionId}`;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `00:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}
