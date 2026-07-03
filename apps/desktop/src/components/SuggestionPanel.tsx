import { Suggestion } from "@meeting-copilot/shared";

interface SuggestionPanelProps {
  suggestions: Suggestion[];
}

export function SuggestionPanel({ suggestions }: SuggestionPanelProps) {
  return (
    <aside className="suggestion-section" aria-label="实时建议">
      <div className="section-heading">
        <h2>实时建议</h2>
        <span>{suggestions.length} 条</span>
      </div>
      <div className="suggestion-list">
        {suggestions.length === 0 ? (
          <p className="empty-state">识别到问题、风险或待办时会出现在这里。</p>
        ) : (
          suggestions.map((suggestion) => (
            <article className="suggestion-card" key={suggestion.id}>
              <div className="suggestion-card-header">
                <h3>{suggestion.title}</h3>
                <span className={`priority priority-${suggestion.priority}`}>
                  {suggestion.priority}
                </span>
              </div>
              {suggestion.problemEssence ? <p>{suggestion.problemEssence}</p> : null}
              {suggestion.risk ? <p className="follow-up">风险：{suggestion.risk}</p> : null}
              <p>{suggestion.recommendedResponse}</p>
              {suggestion.followUpQuestion ? (
                <p className="follow-up">追问：{suggestion.followUpQuestion}</p>
              ) : null}
              {suggestion.actionItem ? (
                <p className="follow-up">待办：{suggestion.actionItem}</p>
              ) : null}
            </article>
          ))
        )}
      </div>
    </aside>
  );
}
