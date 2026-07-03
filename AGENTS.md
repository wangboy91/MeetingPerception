# AGENTS.md

## 项目身份

你正在开发一个桌面端 Meeting Copilot：实时监听本机会议音频，实时转写，识别会议上下文中的问题、风险、决策点、待办，并给出大模型建议。

请把它当成一个工程化产品开发，不要写一次性 demo。

## 工作方式

每次动手前必须：

1. 先阅读 `README.md`；
2. 先阅读 `docs/00_PROJECT_OVERVIEW.md`；
3. 根据当前任务阅读相关设计文档；
4. 如果任务来自 `tasks/PHASE_*.md`，必须严格按该文件的验收标准完成。

## 开发原则

- 先实现可运行闭环，再做优化。
- 每次提交都要保证项目能启动。
- 不要一次性引入过多依赖。
- 不要把业务逻辑写死在 UI 层。
- 音频采集、ASR、VAD、LLM、存储都必须有接口抽象，便于替换。
- 默认本地优先，云端能力必须通过配置打开。
- 所有用户敏感数据默认存本地，不要默认上传。
- 每个模块都要有清晰日志。
- 遇到系统权限问题时，要提供清晰错误提示，而不是静默失败。

## 技术约束

默认技术栈：

```text
Desktop: Tauri + React + TypeScript
Native layer: Rust
AI service: Python + FastAPI + WebSocket
Database: SQLite
ASR: FunASR adapter first, faster-whisper adapter optional
VAD: Silero VAD adapter
LLM: OpenAI-compatible API adapter + optional local Ollama adapter
```

MVP 优先支持：

```text
Windows 10/11
麦克风输入采集
系统输出音频采集
实时转写
实时建议
本地会议记录保存
```

macOS 和 Linux 先保留接口，不要求第一阶段完整实现。

## 代码质量要求

- TypeScript 必须开启 strict。
- Rust 代码必须通过 `cargo fmt` 和 `cargo clippy`。
- Python 代码建议使用 `ruff` 和 `pytest`。
- 不要写超大文件，单文件超过 400 行时优先拆分。
- 不要把 Prompt 散落在业务代码里，统一放在 `services/ai-service/app/prompts/`。
- 所有 WebSocket 消息必须有类型字段和 schema 文档。
- SQLite schema 必须有迁移文件。

## 目录约定

```text
apps/desktop/              # Tauri + React 前端
crates/audio-capture/      # Rust 音频采集库
services/ai-service/       # Python ASR/VAD/LLM 服务
packages/shared/           # TypeScript 共享类型
docs/                      # 工程文档
tasks/                     # Codex 阶段任务
scripts/                   # 开发脚本
```

## 禁止事项

- 不要默认上传用户会议音频。
- 不要在日志中打印完整会议内容，除非 debug 配置显式打开。
- 不要把 API Key 写入代码。
- 不要为了快速实现而跳过权限提示。
- 不要把“录音中”状态隐藏起来。
- 不要把 Speaker 1/2/3 伪装成真实姓名。

## 每个任务完成后输出

完成后请输出：

1. 改了哪些文件；
2. 如何启动；
3. 如何测试；
4. 当前已知限制；
5. 下一步建议。
