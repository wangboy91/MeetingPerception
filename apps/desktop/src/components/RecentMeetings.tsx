import { MeetingSession } from "@meeting-copilot/shared";

interface RecentMeetingsProps {
  meetings: MeetingSession[];
  onOpen: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
}

export function RecentMeetings({ meetings, onOpen, onDelete }: RecentMeetingsProps) {
  return (
    <section className="recent-meetings">
      <div className="section-heading">
        <h2>最近会议</h2>
        <span>{meetings.length} 条</span>
      </div>
      <div className="recent-list">
        {meetings.length === 0 ? (
          <p className="empty-state">暂无本地会议记录</p>
        ) : (
          meetings.map((meeting) => (
            <article className="recent-row" key={meeting.id}>
              <div>
                <strong>{meeting.title ?? "Untitled Meeting"}</strong>
                <p>
                  {meeting.status} · {meeting.startedAt}
                </p>
              </div>
              <div className="recent-actions">
                <button type="button" onClick={() => onOpen(meeting.id)}>
                  查看
                </button>
                <button
                  className="danger-link"
                  type="button"
                  onClick={() => onDelete(meeting.id)}
                >
                  删除
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
