import {
  AudioFramePayload,
  AudioLevel,
  MeetingStatus,
  Suggestion,
  TranscriptSegment,
  WebSocketMessage,
} from "@meeting-copilot/shared";
import { useCallback, useEffect, useRef, useState } from "react";

import { buildMeetingWebSocketUrl } from "../services/aiServiceClient";

export function useMeetingSession(sessionId: string) {
  const [status, setStatus] = useState<MeetingStatus>("connecting");
  const [transcripts, setTranscripts] = useState<TranscriptSegment[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [audioLevels, setAudioLevels] = useState<Partial<Record<AudioLevel["track"], AudioLevel>>>({});
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket(buildMeetingWebSocketUrl(sessionId));
    socketRef.current = socket;

    socket.onopen = () => {
      setConnectionError(null);
      setStatus("recording");
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      const message = JSON.parse(event.data) as WebSocketMessage;

      if (message.type === "meeting.status") {
        const payload = message.payload as { status: MeetingStatus };
        setStatus(payload.status);
      }

      if (message.type === "transcript.final" || message.type === "transcript.partial") {
        setTranscripts((current) => [...current, message.payload as TranscriptSegment]);
      }

      if (message.type === "suggestion.created") {
        setSuggestions((current) => [message.payload as Suggestion, ...current]);
      }

      if (message.type === "audio.level") {
        const payload = message.payload as AudioLevel;
        setAudioLevels((current) => ({ ...current, [payload.track]: payload }));
      }
    };

    socket.onerror = () => {
      setConnectionError("无法连接 127.0.0.1:8765，请先启动 AI Service");
      setStatus("error");
    };

    socket.onclose = () => {
      setStatus((current) => (current === "ended" ? current : "idle"));
    };

    return () => {
      setStatus("ended");
      socketRef.current = null;
      socket.close();
    };
  }, [sessionId]);

  const sendAudioFrame = useCallback((payload: AudioFramePayload) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    socket.send(
      JSON.stringify({
        type: "audio.frame",
        session_id: payload.sessionId,
        timestamp: new Date().toISOString(),
        payload,
      }),
    );
  }, []);

  return { status, transcripts, suggestions, audioLevels, connectionError, sendAudioFrame };
}
