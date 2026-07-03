# 04 仓库结构与工程规范

## 1. 推荐仓库结构

```text
meeting-copilot/
├── AGENTS.md
├── README.md
├── package.json
├── pnpm-workspace.yaml
├── Cargo.toml
├── pyproject.toml
├── apps/
│   └── desktop/
│       ├── src/
│       ├── src-tauri/
│       ├── package.json
│       └── README.md
├── crates/
│   └── audio-capture/
│       ├── src/
│       ├── Cargo.toml
│       └── README.md
├── services/
│   └── ai-service/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   ├── core/
│       │   ├── audio/
│       │   ├── asr/
│       │   ├── vad/
│       │   ├── diarization/
│       │   ├── llm/
│       │   ├── prompts/
│       │   ├── storage/
│       │   └── schemas/
│       ├── tests/
│       ├── pyproject.toml
│       └── README.md
├── packages/
│   └── shared/
│       ├── src/
│       └── package.json
├── docs/
├── tasks/
├── prompts/
└── scripts/
```

## 2. 模块职责

### 2.1 `apps/desktop`

桌面应用。

职责：

- UI；
- 用户设置；
- 设备选择；
- 启停会议；
- WebSocket 连接；
- 展示字幕和建议；
- 调用 Tauri commands；
- 导出文件。

### 2.2 `crates/audio-capture`

Rust 音频采集库。

职责：

- 枚举音频设备；
- 采集麦克风；
- 采集系统输出；
- 音频帧标准化；
- 向上层输出 PCM frame。

### 2.3 `services/ai-service`

Python AI 服务。

职责：

- 提供 REST/WebSocket API；
- 音频流接收；
- VAD；
- ASR；
- Diarization；
- 转写合并；
- 上下文管理；
- 事件识别；
- LLM 建议；
- SQLite 存储。

### 2.4 `packages/shared`

共享类型。

职责：

- WebSocket message type；
- Transcript schema；
- Suggestion schema；
- Settings schema。

## 3. 前端目录建议

```text
apps/desktop/src/
├── main.tsx
├── app/
│   ├── App.tsx
│   └── router.tsx
├── pages/
│   ├── HomePage.tsx
│   ├── MeetingPage.tsx
│   └── SummaryPage.tsx
├── components/
│   ├── DeviceSelector.tsx
│   ├── RecordingStatus.tsx
│   ├── TranscriptTimeline.tsx
│   ├── SuggestionPanel.tsx
│   ├── MeetingControls.tsx
│   └── SettingsDialog.tsx
├── hooks/
│   ├── useMeetingSession.ts
│   ├── useWebSocket.ts
│   └── useAudioDevices.ts
├── services/
│   ├── aiServiceClient.ts
│   └── tauriApi.ts
├── stores/
│   ├── meetingStore.ts
│   └── settingsStore.ts
└── styles/
```

## 4. AI 服务目录建议

```text
services/ai-service/app/
├── main.py
├── api/
│   ├── http.py
│   └── websocket.py
├── core/
│   ├── config.py
│   ├── logging.py
│   └── lifecycle.py
├── audio/
│   ├── frame.py
│   ├── stream_buffer.py
│   └── resample.py
├── vad/
│   ├── base.py
│   └── silero_provider.py
├── asr/
│   ├── base.py
│   ├── funasr_provider.py
│   ├── whisper_provider.py
│   └── mock_provider.py
├── diarization/
│   ├── base.py
│   ├── mock_provider.py
│   └── funasr_provider.py
├── transcript/
│   ├── processor.py
│   ├── segmenter.py
│   └── punctuation.py
├── context/
│   ├── manager.py
│   ├── summarizer.py
│   └── meeting_state.py
├── events/
│   ├── detector.py
│   └── rules.py
├── llm/
│   ├── base.py
│   ├── openai_compatible.py
│   ├── ollama.py
│   └── router.py
├── prompts/
│   ├── event_detector.md
│   ├── suggestion_generator.md
│   └── meeting_summary.md
├── storage/
│   ├── database.py
│   ├── migrations/
│   └── repositories.py
└── schemas/
    ├── transcript.py
    ├── suggestion.py
    ├── meeting.py
    └── websocket.py
```

## 5. 命名规范

### 5.1 WebSocket 消息

统一格式：

```json
{
  "type": "transcript.final",
  "session_id": "...",
  "timestamp": "2026-07-03T10:00:00Z",
  "payload": {}
}
```

### 5.2 Python 类名

- Provider 后缀表示可替换适配器；
- Manager 后缀表示状态管理；
- Processor 后缀表示数据处理；
- Repository 后缀表示数据库访问。

### 5.3 前端组件

- 页面组件：`HomePage`；
- 展示组件：`TranscriptTimeline`；
- Hook：`useMeetingSession`；
- 客户端：`aiServiceClient`。

## 6. 配置文件

建议配置：

```text
~/.meeting-copilot/config.json
```

配置内容：

```json
{
  "asr": {
    "provider": "funasr",
    "model": "paraformer-zh"
  },
  "llm": {
    "provider": "openai-compatible",
    "base_url": "",
    "model": "",
    "api_key_ref": "local-secure-store"
  },
  "privacy": {
    "upload_audio": false,
    "store_transcript": true,
    "debug_log_transcript": false
  }
}
```

## 7. Git 分支建议

```text
main：稳定版本
dev：开发集成
feature/audio-capture
feature/asr-service
feature/llm-suggestion
feature/desktop-ui
```

Codex 开发建议每个阶段一个分支。

## 8. 提交规范

```text
feat: add ai service websocket
fix: handle audio device disconnect
refactor: split transcript processor
chore: add ruff config
docs: update architecture
```

## 9. 运行命令建议

根目录：

```bash
pnpm install
pnpm dev:desktop
pnpm dev:ai
pnpm lint
pnpm test
```

Python 服务：

```bash
cd services/ai-service
uv sync
uv run fastapi dev app/main.py
uv run pytest
```

Rust：

```bash
cargo fmt
cargo clippy
cargo test
```
