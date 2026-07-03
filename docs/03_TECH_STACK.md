# 03 技术选型与低成本方案

## 1. 选型目标

目标不是堆最强技术，而是最低成本跑通可用闭环。

选型原则：

- 开源优先；
- 本地优先；
- 模块可替换；
- 先 Windows；
- Python 负责 AI，Rust 负责系统能力，TypeScript 负责 UI；
- 大模型调用按需触发，避免成本失控。

## 2. 默认技术栈

| 模块 | 默认选型 | 说明 |
|---|---|---|
| 桌面端 | Tauri + React + TypeScript | 轻量、跨平台、Rust 能力强 |
| 音频采集 | Rust + cpal/wasapi bindings | Windows 优先 |
| AI 服务 | Python + FastAPI | 方便接 ASR/VAD/LLM |
| 实时通信 | WebSocket | 推送字幕和建议 |
| 本地数据库 | SQLite | MVP 足够 |
| VAD | Silero VAD | 轻量，CPU 可跑 |
| ASR | FunASR | 中文优先，流式和说话人能力较完整 |
| 备用 ASR | faster-whisper / whisper.cpp | 多语种备用 |
| 说话人分离 | FunASR diarization / pyannote | 第二阶段接入 |
| LLM | OpenAI-compatible API + Ollama | 云端/本地双模式 |
| 包管理 | pnpm + uv/poetry + cargo | 各栈独立 |

## 3. 为什么桌面端选 Tauri

Tauri 适合这个项目的原因：

- 体积比 Electron 小；
- 后端是 Rust，适合做系统音频采集；
- 前端仍然可以用 React；
- 能用系统 WebView；
- 和本地进程通信方便。

备选：Electron。

Electron 优点：

- 快速；
- 桌面能力成熟；
- 生态大。

Electron 缺点：

- 包体积大；
- 长期开销更高；
- 系统层音频采集仍然可能需要 native 模块。

结论：

```text
如果追求最快 demo：Electron。
如果追求工程化产品：Tauri。
```

本项目默认 Tauri。

## 4. 为什么 AI 服务用 Python

因为 ASR、VAD、Diarization、LLM 生态大多在 Python。

Python 服务职责：

- 加载模型；
- 接收音频；
- 处理音频切片；
- 输出转写；
- 调用 LLM；
- 写数据库。

Rust 不要直接承载太多 AI 模型推理，除非后续要极致本地化。

## 5. ASR 选型

### 5.1 FunASR

适合：

- 中文会议；
- 中文标点；
- 中文热词；
- 流式识别；
- 后续说话人分离。

第一版优先。

### 5.2 faster-whisper

适合：

- 多语言；
- Whisper 生态；
- GPU 或 CPU 优化推理。

### 5.3 whisper.cpp

适合：

- 本地纯 C/C++ 部署；
- 低资源环境；
- 后续如果想减少 Python 依赖可考虑。

### 5.4 sherpa-onnx

适合：

- 统一 ONNX Runtime；
- 跨平台；
- 更偏工程化嵌入。

可以作为后续替换目标。

## 6. VAD 选型

默认 Silero VAD。

作用：

```text
过滤静音
切分语音片段
降低 ASR 调用量
降低延迟
降低成本
```

第一版需要实现：

- 输入 PCM frame；
- 输出 speech_start / speech_end；
- 根据 speech segment 调用 ASR。

## 7. LLM 选型

### 7.1 OpenAI-compatible API

必须做成通用接口：

```text
base_url
api_key
model
temperature
max_tokens
```

这样可以接：

- OpenAI；
- OpenRouter；
- 火山方舟；
- 阿里百炼；
- DeepSeek-compatible；
- 本地兼容服务。

### 7.2 Ollama

本地低成本方案。

适合：

- 问题识别；
- 简单总结；
- 私密会议；
- 不联网场景。

不适合：

- 高质量复杂建议；
- 强推理场景；
- 很长上下文。

### 7.3 调用策略

不要每句话调用 LLM。

建议流程：

```text
规则/小模型先判断是否高价值
→ 高价值才调用大模型
→ 建议卡片限制频率
→ 每 3～5 分钟做一次摘要压缩
```

## 8. 数据库选型

MVP 用 SQLite。

原因：

- 本地产品足够；
- 无需安装服务端数据库；
- 易导出；
- 与桌面端兼容好。

后续如果做 SaaS，再上 PostgreSQL。

## 9. 开发工具

建议：

```text
Node: pnpm
Rust: cargo
Python: uv 或 poetry
Format: prettier + rustfmt + ruff
Test: vitest + cargo test + pytest
DB migration: alembic 或 yoyo-migrations
```

## 10. 成本估算策略

### 10.1 本地成本

本地 ASR + 本地 VAD：

```text
API 成本约等于 0
主要成本是用户机器 CPU/GPU
```

### 10.2 云端 LLM 成本

控制成本的方法：

- 只发送最近 2～5 分钟上下文；
- 发送摘要而不是全文；
- 只对高价值事件触发；
- 建议输出限制在 200～500 字；
- 按会议模式切换模型。

### 10.3 云端 ASR 成本

第一版不建议默认云端 ASR。

除非：

- 用户机器性能太弱；
- 要做移动端；
- 要追求最高准确率。

## 11. 第一版最终建议

```text
Tauri + React + TypeScript
Rust audio capture
Python FastAPI AI service
Silero VAD
FunASR
SQLite
OpenAI-compatible LLM adapter
```

这套组合成本低、可控、容易给 Codex 拆任务，也方便后续产品化。
