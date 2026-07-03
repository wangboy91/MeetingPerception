# Meeting Copilot 工程文档包

## 目标

做一个桌面端会议实时辅助软件：

- 同时监听本机麦克风输入和电脑系统输出音频；
- 实时转写会议内容；
- 尽量区分本地用户和远程说话人；
- 自动识别会议语境中的问题、风险、待办、决策点；
- 将高价值上下文投喂大模型，实时给出建议；
- 会后生成会议纪要和结构化记录。

这个产品的核心不是“录音转文字”，而是：

> 会议实时感知 + 语境理解 + 决策辅助。

## 给 Codex 的使用方式

建议把本文件夹内容放到项目仓库根目录，例如：

```text
meeting-copilot/
├── AGENTS.md
├── README.md
├── docs/
├── prompts/
└── tasks/
```

然后让 Codex 按下面顺序执行：

1. 先读 `AGENTS.md`；
2. 再读 `docs/00_PROJECT_OVERVIEW.md`；
3. 再读 `docs/01_PRD.md`；
4. 再读 `docs/02_ARCHITECTURE.md`；
5. 最后按 `tasks/PHASE_*.md` 分阶段开发。

## 文档目录

| 文档 | 用途 |
|---|---|
| `AGENTS.md` | Codex 项目级工作规范 |
| `docs/00_PROJECT_OVERVIEW.md` | 项目总览与边界 |
| `docs/01_PRD.md` | 产品需求文档 |
| `docs/02_ARCHITECTURE.md` | 技术架构设计 |
| `docs/03_TECH_STACK.md` | 技术选型与低成本方案 |
| `docs/04_REPO_STRUCTURE.md` | 仓库结构与工程规范 |
| `docs/05_AUDIO_CAPTURE.md` | 音频采集设计 |
| `docs/06_ASR_DIARIZATION.md` | ASR、VAD、说话人分离设计 |
| `docs/07_LLM_COPILOT_ENGINE.md` | 大模型建议引擎设计 |
| `docs/08_API_AND_DATA_MODEL.md` | API、WebSocket、数据库模型 |
| `docs/09_FRONTEND_UX.md` | 前端交互与界面设计 |
| `docs/10_SECURITY_PRIVACY.md` | 隐私、安全、合规设计 |
| `docs/11_TESTING_OBSERVABILITY.md` | 测试与可观测性 |
| `docs/12_PACKAGING_DEPLOYMENT.md` | 打包、部署、发布 |
| `tasks/PHASE_0_BOOTSTRAP.md` | 阶段 0：项目骨架 |
| `tasks/PHASE_1_AUDIO_ASR.md` | 阶段 1：音频采集与实时转写 |
| `tasks/PHASE_2_TRANSCRIPT_STORAGE.md` | 阶段 2：转写流与本地存储 |
| `tasks/PHASE_3_LLM_SUGGESTION.md` | 阶段 3：大模型建议引擎 |
| `tasks/PHASE_4_DIARIZATION.md` | 阶段 4：说话人分离 |
| `tasks/PHASE_5_POLISH_RELEASE.md` | 阶段 5：产品化与发布 |
| `prompts/CODEX_START_PROMPT.md` | 第一次交给 Codex 的总启动提示词 |
| `prompts/CODEX_REVIEW_PROMPT.md` | 让 Codex 自检和重构的提示词 |

## 建议的第一版范围

第一版只做 Windows 优先，macOS/Linux 作为后续扩展。

MVP 必须跑通：

```text
桌面端启动
选择麦克风
监听系统输出
实时切片
本地 VAD
本地 ASR
实时字幕
本地保存
问题识别
大模型建议
```

第一版可以不强求：

```text
精准识别每个远程参会人的真实姓名
接入 Zoom/Teams/飞书官方会议 SDK
团队协作后台
云端多租户
浏览器插件
移动端
```

## 默认技术路线

```text
Desktop: Tauri + React + TypeScript
Native: Rust audio capture layer
AI Service: Python + FastAPI + WebSocket
ASR: FunASR first, faster-whisper optional
VAD: Silero VAD
LLM: 本地 Ollama + 云端 OpenAI-compatible API 混合
DB: SQLite
Packaging: Tauri bundle
```

## 开发原则

1. 先跑通真实音频流，不要先做漂亮 UI。
2. 先区分“我”和“远程混音”，不要一开始追求精准到人名。
3. 大模型只处理高价值片段，不要每句话都调用。
4. 所有模块必须可替换：ASR、LLM、VAD、Diarization 都要通过接口抽象。
5. 默认本地优先，用户可选云端增强。
