import { TranscriptSegment } from "@meeting-copilot/shared";

interface TranscriptTimelineProps {
  transcripts: TranscriptSegment[];
}

export function TranscriptTimeline({ transcripts }: TranscriptTimelineProps) {
  return (
    <section className="timeline-section" aria-label="实时转写时间轴">
      <div className="section-heading">
        <h2>实时转写</h2>
        <span>{transcripts.length} 条</span>
      </div>
      <div className="timeline-list">
        {transcripts.length === 0 ? (
          <p className="empty-state">等待 AI Service 推送 mock transcript...</p>
        ) : (
          transcripts.map((item) => (
            <article className="transcript-row" key={item.id}>
              <time>{item.time}</time>
              <div>
                <strong>{item.speaker}</strong>
                <p>{item.text}</p>
              </div>
              <span className="final-badge">{item.isFinal ? "Final" : "Partial"}</span>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
