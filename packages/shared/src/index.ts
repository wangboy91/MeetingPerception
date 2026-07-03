export type MeetingStatus = "idle" | "connecting" | "recording" | "paused" | "ended" | "error";

export type SpeakerLabel = "Me" | "Remote" | `Speaker ${number}`;

export type AudioTrack = "mic" | "system";

export type AssistantRole = "tech-review" | "product-review" | "sales" | "management";

export interface AssistantRoleOption {
  id: AssistantRole;
  label: string;
  description: string;
}

export interface TranscriptSegment {
  id: string;
  sessionId: string;
  segmentId?: string;
  time: string;
  speaker: SpeakerLabel;
  track?: AudioTrack;
  startMs?: number;
  endMs?: number;
  confidence?: number;
  text: string;
  isFinal: boolean;
  createdAt: string;
}

export type SuggestionPriority = "low" | "medium" | "high";

export interface Suggestion {
  id: string;
  sessionId: string;
  priority: SuggestionPriority;
  title: string;
  problemEssence?: string;
  rationale: string;
  risk?: string;
  recommendedResponse: string;
  suggestedReply?: string;
  followUpQuestion?: string;
  actionItem?: string;
  eventType?: string;
  createdAt: string;
}

export interface AudioFramePayload {
  sessionId: string;
  track: AudioTrack;
  timestampMs: number;
  sampleRate: 16000;
  channels: 1;
  format: "pcm_s16le";
  seq: number;
  rms: number;
  data: string;
}

export interface AudioLevel {
  track: AudioTrack;
  level: number;
  isSpeech: boolean;
  framesReceived: number;
}

export interface Speaker {
  id: string;
  meetingId: string;
  label: string;
  source: AudioTrack | string;
  displayName?: string | null;
}

export interface MeetingSession {
  id: string;
  status: MeetingStatus;
  startedAt: string;
  title?: string;
  mode?: string;
  userRole?: string;
  endedAt?: string | null;
}

export interface WebSocketMessage<TPayload = unknown> {
  type:
    | "meeting.status"
    | "transcript.partial"
    | "transcript.final"
    | "analysis.event"
    | "suggestion.created"
    | "summary.updated"
    | "audio.level"
    | "audio.frame"
    | "error";
  sessionId: string;
  timestamp: string;
  payload: TPayload;
}
