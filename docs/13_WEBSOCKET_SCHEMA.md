# 13 WebSocket Schema

All WebSocket messages use a typed envelope:

```json
{
  "type": "transcript.final",
  "session_id": "session-uuid",
  "timestamp": "2026-07-03T03:30:00Z",
  "payload": {}
}
```

## Message Types

- `meeting.status`
- `transcript.partial`
- `transcript.final`
- `analysis.event`
- `suggestion.created`
- `summary.updated`
- `audio.frame`
- `audio.level`
- `error`

## Transcript Payload

```json
{
  "id": "transcript-uuid",
  "sessionId": "session-uuid",
  "time": "00:03:12",
  "speaker": "Me",
  "text": "这个需求如果下周上线，会不会影响支付流程？",
  "isFinal": true,
  "createdAt": "2026-07-03T03:30:00Z"
}
```

## Suggestion Payload

```json
{
  "id": "suggestion-uuid",
  "sessionId": "session-uuid",
  "priority": "high",
  "title": "上线风险需要拆解确认",
  "rationale": "当前讨论涉及支付链路、测试时间和回滚边界。",
  "recommendedResponse": "建议先明确影响范围，再确认灰度和回滚方案。",
  "followUpQuestion": "这次变更是否覆盖退款、老订单和异常补偿流程？",
  "createdAt": "2026-07-03T03:30:00Z"
}
```

## Audio Frame Payload

The desktop client sends `audio.frame` messages to the AI Service.

```json
{
  "sessionId": "session-uuid",
  "track": "mic",
  "timestampMs": 1780000000000,
  "sampleRate": 16000,
  "channels": 1,
  "format": "pcm_s16le",
  "seq": 42,
  "rms": 0.06,
  "data": "base64-pcm-s16le"
}
```

Native Tauri capture emits the same frame shape to the frontend with event name:

```text
audio.frame.native
```

The frontend may forward that payload to the AI Service as `audio.frame`.

## Audio Level Payload

The AI Service returns `audio.level` after VAD processing.

```json
{
  "track": "mic",
  "level": 0.06,
  "isSpeech": true,
  "framesReceived": 42
}
```
