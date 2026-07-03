# 08 API、WebSocket 与数据模型

## 1. API 设计原则

- 本地服务优先；
- UI 与 AI service 解耦；
- WebSocket 推送实时数据；
- REST 处理配置、历史和导出；
- 所有消息必须有明确 type；
- 所有数据必须有 session_id。

## 2. REST API

### 2.1 健康检查

```http
GET /health
```

响应：

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### 2.2 创建会议

```http
POST /api/meetings
```

请求：

```json
{
  "title": "需求评审",
  "mode": "technical_review",
  "user_role": "backend_engineer"
}
```

响应：

```json
{
  "session_id": "uuid",
  "status": "created"
}
```

### 2.3 开始会议

```http
POST /api/meetings/{session_id}/start
```

### 2.4 结束会议

```http
POST /api/meetings/{session_id}/stop
```

响应：

```json
{
  "session_id": "uuid",
  "status": "stopped",
  "summary_status": "pending"
}
```

### 2.5 获取会议详情

```http
GET /api/meetings/{session_id}
```

### 2.6 获取会议转写

```http
GET /api/meetings/{session_id}/transcripts
```

### 2.7 获取建议

```http
GET /api/meetings/{session_id}/suggestions
```

### 2.8 导出 Markdown

```http
GET /api/meetings/{session_id}/export?format=markdown
```

## 3. WebSocket

连接地址：

```text
ws://localhost:8765/ws/meetings/{session_id}
```

### 3.1 通用消息格式

```json
{
  "type": "transcript.final",
  "session_id": "uuid",
  "timestamp": "2026-07-03T12:00:00Z",
  "payload": {}
}
```

### 3.2 会议状态

```json
{
  "type": "meeting.status",
  "session_id": "uuid",
  "timestamp": "...",
  "payload": {
    "status": "recording",
    "mic_active": true,
    "system_active": true,
    "asr_ready": true,
    "llm_ready": true
  }
}
```

### 3.3 音频状态

```json
{
  "type": "audio.level",
  "session_id": "uuid",
  "timestamp": "...",
  "payload": {
    "track": "mic",
    "level": 0.72,
    "is_speech": true
  }
}
```

### 3.4 临时转写

```json
{
  "type": "transcript.partial",
  "session_id": "uuid",
  "timestamp": "...",
  "payload": {
    "segment_id": "uuid",
    "speaker_label": "Me",
    "track": "mic",
    "text": "这个需求如果下周",
    "start_ms": 10000,
    "end_ms": 12000
  }
}
```

### 3.5 最终转写

```json
{
  "type": "transcript.final",
  "session_id": "uuid",
  "timestamp": "...",
  "payload": {
    "segment_id": "uuid",
    "speaker_label": "Me",
    "track": "mic",
    "text": "这个需求如果下周上线，会不会影响支付流程？",
    "start_ms": 10000,
    "end_ms": 14500,
    "confidence": 0.92
  }
}
```

### 3.6 分析事件

```json
{
  "type": "analysis.event",
  "session_id": "uuid",
  "timestamp": "...",
  "payload": {
    "event_id": "uuid",
    "trigger_segment_id": "uuid",
    "event_type": "risk",
    "priority": "high",
    "reason": "涉及上线风险和支付链路"
  }
}
```

### 3.7 建议卡片

```json
{
  "type": "suggestion.created",
  "session_id": "uuid",
  "timestamp": "...",
  "payload": {
    "suggestion_id": "uuid",
    "trigger_segment_id": "uuid",
    "title": "先确认支付链路影响范围",
    "problem_essence": "问题本质是上线时间和支付稳定性的冲突。",
    "risk": "未确认回滚方案可能影响线上支付。",
    "suggested_reply": "我们先拆成影响范围和回滚方案两个问题确认。支付链路如果有改动，建议先灰度验证。",
    "follow_up_question": "这次改动是否影响退款和老订单？",
    "action_item": "后端负责人梳理支付链路影响点。",
    "priority": "high"
  }
}
```

### 3.8 错误

```json
{
  "type": "error",
  "session_id": "uuid",
  "timestamp": "...",
  "payload": {
    "code": "ASR_MODEL_LOAD_FAILED",
    "message": "ASR 模型加载失败，请检查模型配置。",
    "recoverable": true
  }
}
```

## 4. SQLite 数据模型

### 4.1 meetings

```sql
CREATE TABLE meetings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    mode TEXT NOT NULL,
    user_role TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 4.2 transcripts

```sql
CREATE TABLE transcripts (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    speaker_id TEXT,
    speaker_label TEXT NOT NULL,
    track TEXT NOT NULL,
    text TEXT NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    confidence REAL,
    is_final INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
```

### 4.3 suggestions

```sql
CREATE TABLE suggestions (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    trigger_segment_id TEXT,
    title TEXT NOT NULL,
    problem_essence TEXT,
    risk TEXT,
    suggested_reply TEXT,
    follow_up_question TEXT,
    action_item TEXT,
    priority TEXT NOT NULL,
    raw_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
```

### 4.4 meeting_state_snapshots

```sql
CREATE TABLE meeting_state_snapshots (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    current_topic TEXT,
    summary TEXT,
    decisions_json TEXT,
    risks_json TEXT,
    todos_json TEXT,
    open_questions_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
```

### 4.5 speakers

```sql
CREATE TABLE speakers (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    label TEXT NOT NULL,
    source TEXT NOT NULL,
    display_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
```

### 4.6 settings

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

## 5. Python Schema 建议

用 Pydantic：

```python
class TranscriptFinalPayload(BaseModel):
    segment_id: str
    speaker_label: str
    track: Literal["mic", "system"]
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None
```

## 6. 前端 TypeScript 类型

```ts
export type WsMessage<T = unknown> = {
  type: string;
  session_id: string;
  timestamp: string;
  payload: T;
};

export type TranscriptFinalPayload = {
  segment_id: string;
  speaker_label: string;
  track: 'mic' | 'system';
  text: string;
  start_ms: number;
  end_ms: number;
  confidence?: number;
};
```

## 7. 导出 Markdown 格式

```markdown
# 需求评审会议纪要

## 摘要

...

## 决策

- ...

## 待办

- [ ] 王：确认支付链路影响范围，下周一前

## 风险

- ...

## 原始转写

[00:01:12] Me：...
[00:01:18] Remote：...
```

## 8. 验收标准

- REST API 可创建/开始/结束会议；
- WebSocket 可推送 mock transcript；
- SQLite 能保存 meeting/transcript/suggestion；
- UI 能从 WebSocket 接收并渲染；
- 导出 Markdown 可用。
