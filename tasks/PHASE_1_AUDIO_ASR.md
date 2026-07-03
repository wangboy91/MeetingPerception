# Phase 1：音频采集与实时转写

## 目标

跑通从麦克风音频到实时转写的第一条真实链路。

```text
Mic Audio → VAD → ASR/Mock ASR → Transcript → WebSocket → UI
```

## 输入文档

Codex 开始前必须阅读：

- `docs/05_AUDIO_CAPTURE.md`
- `docs/06_ASR_DIARIZATION.md`
- `docs/08_API_AND_DATA_MODEL.md`

## 任务清单

### 1. 音频设备枚举

桌面端支持：

- 获取麦克风设备列表；
- 显示默认设备；
- 选择设备。

如果系统音频采集暂时没完成，先保留 UI 入口并标记为 later。

### 2. 麦克风采集

实现 mic track 采集。

要求：

- 采集 PCM；
- 重采样到 16k mono；
- 推送到 AI Service；
- UI 显示音量。

### 3. VAD Provider

实现：

```text
VadProvider base
SileroVadProvider
MockVadProvider
```

MVP 可先 Mock，再接 Silero。

### 4. ASR Provider

实现：

```text
AsrProvider base
MockAsrProvider
FunAsrProvider skeleton
```

第一步必须保留 Mock，避免模型环境阻塞前端开发。

### 5. Transcript Processor

实现：

- speech segment 合并；
- speaker_label = Me；
- transcript.final WebSocket 推送。

### 6. UI 实时字幕

MeetingPage 展示：

- speaker；
- time；
- text；
- final 状态。

## 验收标准

- 说话时 UI 音量条有变化；
- AI Service 能收到音频 frame；
- VAD 能识别 speech/silence；
- ASR mock 能生成 transcript.final；
- UI 能实时显示转写；
- 运行 10 分钟不崩溃。

## 注意

第一阶段不追求系统输出采集。

第一阶段不追求说话人分离。

第一阶段不追求 ASR 准确率，先保证链路。
