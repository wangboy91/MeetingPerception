import { MeetingSession, Speaker, Suggestion, TranscriptSegment } from "@meeting-copilot/shared";
import { useEffect, useState } from "react";

import {
  exportMeetingMarkdownUrl,
  getMeeting,
  getSpeakers,
  getSuggestions,
  getTranscripts,
  renameSpeaker,
} from "../services/aiServiceClient";

interface SummaryPageProps {
  sessionId: string;
  onBackHome: () => void;
}

export function SummaryPage({ sessionId, onBackHome }: SummaryPageProps) {
  const [meeting, setMeeting] = useState<MeetingSession | null>(null);
  const [transcripts, setTranscripts] = useState<TranscriptSegment[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [nextMeeting, nextTranscripts, nextSuggestions, nextSpeakers] = await Promise.all([
          getMeeting(sessionId),
          getTranscripts(sessionId),
          getSuggestions(sessionId),
          getSpeakers(sessionId),
        ]);
        setMeeting(nextMeeting);
        setTranscripts(nextTranscripts);
        setSuggestions(nextSuggestions);
        setSpeakers(nextSpeakers);
        setError(null);
      } catch {
        setError("无法加载会后记录，请确认 AI Service 仍在运行");
      }
    }

    void load();
  }, [sessionId]);

  async function handleRenameSpeaker(speakerId: string, displayName: string) {
    await renameSpeaker(sessionId, speakerId, displayName);
    const [nextSpeakers, nextTranscripts] = await Promise.all([
      getSpeakers(sessionId),
      getTranscripts(sessionId),
    ]);
    setSpeakers(nextSpeakers);
    setTranscripts(nextTranscripts);
  }

  return (
    <main className="summary-shell">
      <header className="summary-header">
        <div>
          <p className="eyebrow">Meeting Summary</p>
          <h1>{meeting?.title ?? "会议记录"}</h1>
          <p>{meeting ? `${meeting.startedAt} - ${meeting.endedAt ?? "未结束"}` : sessionId}</p>
        </div>
        <div className="summary-actions">
          <a className="download-action" href={exportMeetingMarkdownUrl(sessionId)}>
            导出 Markdown
          </a>
          <button type="button" onClick={onBackHome}>
            回到首页
          </button>
        </div>
      </header>

      {error ? <p className="device-error">{error}</p> : null}

      <section className="summary-grid">
        <section className="timeline-section">
          <div className="section-heading">
            <h2>原始转写</h2>
            <span>{transcripts.length} 条</span>
          </div>
          {speakers.length > 0 ? (
            <div className="speaker-editor">
              {speakers.map((speaker) => (
                <label key={speaker.id}>
                  <span>{speaker.displayName || speaker.label}</span>
                  <input
                    defaultValue={speaker.displayName ?? ""}
                    placeholder="手动命名"
                    onBlur={(event) => {
                      void handleRenameSpeaker(speaker.id, event.target.value);
                    }}
                  />
                </label>
              ))}
            </div>
          ) : null}
          <div className="timeline-list">
            {transcripts.length === 0 ? (
              <p className="empty-state">暂无转写记录</p>
            ) : (
              transcripts.map((item) => (
                <article className="transcript-row" key={item.id}>
                  <time>{item.time}</time>
                  <div>
                    <strong>{item.speaker}</strong>
                    <p>{item.text}</p>
                  </div>
                  <span className="final-badge">{item.track ?? "mic"}</span>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="suggestion-section">
          <div className="section-heading">
            <h2>建议</h2>
            <span>{suggestions.length} 条</span>
          </div>
          <div className="suggestion-list">
            {suggestions.length === 0 ? (
              <p className="empty-state">暂无建议记录</p>
            ) : (
              suggestions.map((item) => (
                <article className="suggestion-card" key={item.id}>
                  <div className="suggestion-card-header">
                    <h3>{item.title}</h3>
                    <span className={`priority priority-${item.priority}`}>{item.priority}</span>
                  </div>
                  {item.problemEssence ? <p>{item.problemEssence}</p> : null}
                  {item.risk ? <p className="follow-up">风险：{item.risk}</p> : null}
                  <p>{item.recommendedResponse}</p>
                  {item.followUpQuestion ? <p className="follow-up">追问：{item.followUpQuestion}</p> : null}
                  {item.actionItem ? <p className="follow-up">待办：{item.actionItem}</p> : null}
                </article>
              ))
            )}
          </div>
        </section>
      </section>
    </main>
  );
}
