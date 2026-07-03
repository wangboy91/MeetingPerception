from app.storage.repositories import SuggestionRepository, TranscriptRepository

DECISION_HINTS = ["决定", "确认", "定下来", "结论", "拍板"]
TODO_HINTS = ["负责", "跟进", "确认一下", "owner", "下周", "今天", "明天"]
RISK_HINTS = ["风险", "影响", "回滚", "异常", "担心", "不确定", "来不及"]
QUESTION_HINTS = ["吗", "是否", "会不会", "怎么", "为什么", "?"]


def export_markdown(meeting: dict, transcripts: list[dict], suggestions: list[dict]) -> str:
    summary = build_structured_summary(transcripts, suggestions)
    lines = [
        f"# {meeting['title']}",
        "",
        "## 基本信息",
        "",
        f"- 状态：{meeting['status']}",
        f"- 开始时间：{meeting.get('started_at') or '-'}",
        f"- 结束时间：{meeting.get('ended_at') or '-'}",
        "",
        "## 摘要",
        "",
        summary["summary"],
        "",
        "## 决策",
        "",
        *_format_list(summary["decisions"]),
        "",
        "## 待办",
        "",
        *_format_list(summary["action_items"]),
        "",
        "## 风险",
        "",
        *_format_list(summary["risks"]),
        "",
        "## 未解决问题",
        "",
        *_format_list(summary["open_questions"]),
        "",
        "## 建议",
        "",
    ]

    if suggestions:
        for item in suggestions:
            lines.append(f"- [{item['priority']}] {item['title']}")
            if item.get("suggested_reply"):
                lines.append(f"  - 建议回应：{item['suggested_reply']}")
            if item.get("follow_up_question"):
                lines.append(f"  - 建议追问：{item['follow_up_question']}")
    else:
        lines.append("- 暂无建议")

    lines.extend(["", "## 原始转写", ""])
    if transcripts:
        for item in transcripts:
            seconds = int(item["end_ms"] or item["start_ms"] or 0) // 1000
            timestamp = f"00:{seconds // 60:02d}:{seconds % 60:02d}"
            speaker = item.get("display_speaker_label") or item["speaker_label"]
            lines.append(f"[{timestamp}] {speaker}：{item['text']}")
    else:
        lines.append("暂无转写")

    lines.append("")
    return "\n".join(lines)


def export_meeting_markdown(meeting: dict) -> str:
    transcript_repo = TranscriptRepository()
    suggestion_repo = SuggestionRepository()
    transcripts = transcript_repo.list_for_meeting(meeting["id"])
    suggestions = suggestion_repo.list_for_meeting(meeting["id"])
    return export_markdown(meeting, transcripts, suggestions)


def build_structured_summary(transcripts: list[dict], suggestions: list[dict]) -> dict[str, list[str] | str]:
    transcript_texts = [item["text"] for item in transcripts]
    decisions = _collect_by_keywords(transcript_texts, DECISION_HINTS)
    todos = _collect_by_keywords(transcript_texts, TODO_HINTS)
    risks = _collect_by_keywords(transcript_texts, RISK_HINTS)
    open_questions = _collect_by_keywords(transcript_texts, QUESTION_HINTS)

    for item in suggestions:
        if item.get("suggested_reply"):
            todos.append(item["suggested_reply"])
        if item.get("risk"):
            risks.append(item["risk"])
        if item.get("follow_up_question"):
            open_questions.append(item["follow_up_question"])

    first_items = transcript_texts[:3]
    summary = "；".join(first_items) if first_items else "暂无摘要。"
    return {
        "summary": summary,
        "decisions": _unique_or_empty(decisions),
        "action_items": _unique_or_empty(todos),
        "risks": _unique_or_empty(risks),
        "open_questions": _unique_or_empty(open_questions),
    }


def _collect_by_keywords(texts: list[str], keywords: list[str]) -> list[str]:
    return [text for text in texts if any(keyword in text for keyword in keywords)]


def _unique_or_empty(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result or ["暂无"]


def _format_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]
