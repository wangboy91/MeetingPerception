from dataclasses import dataclass
from typing import Literal

EventType = Literal[
    "question",
    "risk",
    "decision",
    "action_item",
    "requirement_change",
    "technical_unknown",
    "time_conflict",
    "scope_conflict",
]
Priority = Literal["low", "medium", "high"]

QUESTION_KEYWORDS = ["吗", "是不是", "能不能", "是否", "怎么", "为什么", "会不会", "?"]
RISK_KEYWORDS = ["风险", "影响", "来不及", "不确定", "线上", "回滚", "异常", "兼容", "担心"]
TODO_KEYWORDS = ["谁来", "下周", "今天", "明天", "负责", "跟进", "确认一下", "owner"]
DECISION_KEYWORDS = ["决定", "确认", "定下来", "就这么", "结论", "拍板"]
REQUIREMENT_CHANGE_KEYWORDS = ["需求变更", "改一下", "新增", "调整范围", "范围变了"]
TIME_CONFLICT_KEYWORDS = ["延期", "赶不上", "时间不够", "下周上线", "本周上线"]
SCOPE_CONFLICT_KEYWORDS = ["范围", "边界", "都要做", "先不做", "一期"]


@dataclass(frozen=True)
class DetectedEvent:
    should_suggest: bool
    event_type: EventType
    priority: Priority
    reason: str


class EventDetector:
    def detect(self, text: str) -> DetectedEvent:
        normalized = text.strip()
        matches: list[tuple[EventType, Priority, str]] = []

        if _contains_any(normalized, RISK_KEYWORDS):
            matches.append(("risk", "high", "当前发言涉及风险、影响范围或异常处理"))
        if _contains_any(normalized, TIME_CONFLICT_KEYWORDS):
            matches.append(("time_conflict", "high", "当前发言涉及交付时间冲突"))
        if _contains_any(normalized, SCOPE_CONFLICT_KEYWORDS):
            matches.append(("scope_conflict", "medium", "当前发言涉及需求范围或边界"))
        if _contains_any(normalized, REQUIREMENT_CHANGE_KEYWORDS):
            matches.append(("requirement_change", "high", "当前发言涉及需求变更"))
        if _contains_any(normalized, QUESTION_KEYWORDS):
            matches.append(("question", "medium", "当前发言包含需要现场回应的问题"))
        if _contains_any(normalized, TODO_KEYWORDS):
            matches.append(("action_item", "medium", "当前发言可能形成待办或责任人确认"))
        if _contains_any(normalized, DECISION_KEYWORDS):
            matches.append(("decision", "medium", "当前发言可能形成决策点"))

        if not matches:
            return DetectedEvent(False, "question", "low", "未命中高价值会议事件")

        event_type, priority, reason = sorted(matches, key=lambda item: _priority_score(item[1]))[-1]
        return DetectedEvent(True, event_type, priority, reason)


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _priority_score(priority: Priority) -> int:
    return {"low": 1, "medium": 2, "high": 3}[priority]
