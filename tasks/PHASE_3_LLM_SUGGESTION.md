# Phase 3：大模型建议引擎

## 目标

实现会议中的实时建议。

```text
Transcript → Event Detector → Context Manager → LLM → Suggestion Card
```

## 输入文档

- `docs/07_LLM_COPILOT_ENGINE.md`
- `docs/08_API_AND_DATA_MODEL.md`
- `docs/09_FRONTEND_UX.md`

## 任务清单

### 1. Event Detector

实现规则识别：

- question；
- risk；
- action_item；
- decision；
- requirement_change。

输出：

```json
{
  "should_suggest": true,
  "event_type": "risk",
  "priority": "high",
  "reason": "..."
}
```

### 2. Context Manager

实现：

- 最近 5 分钟 transcript buffer；
- 当前 topic；
- decisions；
- risks；
- todos；
- open_questions。

### 3. LLM Provider

实现：

- OpenAI-compatible Provider；
- Mock LLM Provider；
- JSON parse/repair；
- timeout；
- retry once。

### 4. Prompt 文件化

Prompt 放在：

```text
services/ai-service/app/prompts/
```

至少包括：

- `event_detector.md`
- `suggestion_generator.md`
- `meeting_summary.md`

### 5. UI 建议卡片

展示：

- title；
- problem_essence；
- risk；
- suggested_reply；
- follow_up_question；
- action_item；
- priority。

## 验收标准

- mock transcript 中出现问题句时能触发 suggestion；
- LLM 失败不影响转写；
- 建议写入 SQLite；
- UI 能展示建议卡片；
- 60 秒内同类型建议不刷屏；
- 可以关闭建议。
