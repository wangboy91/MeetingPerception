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

## Phase 0 启动说明

当前仓库已经具备最小 monorepo 骨架：

```text
apps/desktop/              # React + TypeScript + Tauri 壳
crates/audio-capture/      # Rust 音频采集接口与 mock provider
services/ai-service/       # FastAPI + WebSocket mock transcript
packages/shared/           # WebSocket、Transcript、Suggestion 共享类型
```

### 安装依赖

本项目推荐通过 Node.js 自带的 Corepack 调用 pnpm。这样会使用 `package.json` 中声明的 pnpm 版本，避免本机没有全局 `pnpm` 或版本不一致。

```bash
corepack pnpm install
cd services/ai-service
python -m pip install -e ".[dev]"
```

### 启动 AI Service

```bash
corepack pnpm dev:ai
```

服务默认监听：

```text
http://127.0.0.1:8765
ws://127.0.0.1:8765/ws/meetings/{session_id}
```

健康检查：

```bash
curl http://127.0.0.1:8765/health
```

### 启动桌面前端

```bash
corepack pnpm dev:desktop
```

浏览器打开：

```text
http://127.0.0.1:1420
```

点击“开始会议”后，前端会创建本地 mock meeting session，并连接 AI Service WebSocket。AI Service 每 2 秒推送一条 mock transcript，遇到风险句子时推送一条 mock suggestion。

### 质量检查

```bash
corepack pnpm lint
corepack pnpm test
cargo fmt --all --check
cargo clippy --workspace --all-targets
```

Phase 0 暂不实现真实音频采集、真实 ASR、SQLite 存储和 LLM 调用；这些能力已经保留接口边界，后续阶段接入。

## Phase 1 当前音频链路

当前已经接入第一条真实麦克风链路。运行在 Tauri 里时优先使用 Rust native capture；运行在普通浏览器里时使用 Web Mic fallback：

```text
Rust cpal Mic Capture 或 Browser Mic Capture
→ 16k mono PCM frame
→ AI Service WebSocket audio.frame
→ Mock VAD
→ Mock ASR
→ transcript.final / audio.level
→ Desktop UI
```

验证方式：

1. 启动 AI Service：

   ```bash
   corepack pnpm dev:ai
   ```

2. 启动桌面前端：

   ```bash
   corepack pnpm dev:desktop
   ```

3. 打开 `http://127.0.0.1:1420`。
4. 点击“授权并刷新麦克风”，选择麦克风。
5. 点击“开始会议”，浏览器授权麦克风后开始说话。
6. 会议页 Mic 音量条会随声音变化，AI Service 收到语音段后会通过 Mock ASR 生成 `transcript.final`。

当前限制：

- ASR 仍是 Mock Provider，不是真实 FunASR。
- VAD 仍是 RMS 阈值 Mock Provider，不是真实 Silero。
- Windows/macOS 麦克风 native capture 已接入 Rust `cpal` provider，并通过 Tauri `audio.frame.native` 事件向前端冒泡音频帧。
- 前端在 Tauri 环境中优先调用 native capture；如果 native 不可用或运行在浏览器中，会回退到 Browser Mic Capture。
- Windows 系统输出 loopback 已保留协议和 UI 入口，后续接 WASAPI loopback provider。
- macOS 系统输出采集已保留 provider 位置，后续优先评估 ScreenCaptureKit；如果权限或系统版本限制较多，再支持 BlackHole 等虚拟音频设备方案。
- 浏览器麦克风采集仍作为开发 fallback，便于没有 Rust 工具链时验证 AI Service 音频链路。

Native capture 支持计划：

| 能力 | Windows | macOS |
|---|---|---|
| 麦克风设备枚举 | `cpal` provider | `cpal` provider |
| 麦克风采集 | `cpal` provider | `cpal` provider |
| 系统输出采集 | WASAPI loopback 待接入 | ScreenCaptureKit/虚拟音频待接入 |
| 音频帧出口 | Tauri `audio.frame.native` event | Tauri `audio.frame.native` event |

## Phase 2 当前本地存储链路

当前已经接入 SQLite 本地存储：

```text
POST /api/meetings
→ SQLite meetings
→ WebSocket transcript.final / suggestion.created
→ SQLite transcripts / suggestions
→ 会后页面
→ Markdown 导出
```

默认数据库路径：

```text
services/ai-service/data/meeting_copilot.sqlite3
```

可通过环境变量覆盖：

```bash
MEETING_COPILOT_DB_PATH=/path/to/meeting_copilot.sqlite3
```

已支持 API：

```text
GET    /api/meetings
POST   /api/meetings
GET    /api/meetings/{session_id}
POST   /api/meetings/{session_id}/stop
GET    /api/meetings/{session_id}/transcripts
GET    /api/meetings/{session_id}/suggestions
GET    /api/meetings/{session_id}/export?format=markdown
DELETE /api/meetings/{session_id}
```

结束会议后前端会进入会后页面，展示已保存的原始转写和建议，并可以导出 Markdown。

隐私边界：

- 默认只保存会议元数据、转写文本和建议；
- 默认不保存原始音频；
- 日志不要打印完整会议内容，除非后续显式开启 debug 配置。

## Phase 3 当前实时建议引擎

当前建议链路：

```text
transcript.final
→ Rule Event Detector
→ Context Manager
→ LLM Router
→ suggestion.created
→ SQLite suggestions
→ UI 建议卡片 / Markdown 导出
```

已支持事件类型：

```text
question
risk
decision
action_item
requirement_change
technical_unknown
time_conflict
scope_conflict
```

LLM Provider：

```text
mock
openai-compatible
anthropic
```

默认使用 `mock`，不会调用云端模型。启用云端模型时只发送必要文本上下文，不发送音频、不发送全文会议记录。

### OpenAI-compatible 配置

```bash
MEETING_COPILOT_LLM_PROVIDER=openai-compatible
MEETING_COPILOT_LLM_BASE_URL=https://example.com/v2
MEETING_COPILOT_LLM_MODEL=your-model
MEETING_COPILOT_LLM_API_KEY=your-api-key
```

也兼容：

```bash
OPENAI_BASE_URL=https://example.com/v2
MODEL=your-model
```

### Anthropic 配置

```bash
MEETING_COPILOT_LLM_PROVIDER=anthropic
MEETING_COPILOT_LLM_BASE_URL=https://example.com/anthropic
MEETING_COPILOT_LLM_MODEL=your-model
MEETING_COPILOT_LLM_API_KEY=your-api-key
```

也兼容：

```bash
ANTHROPIC_BASE_URL=https://example.com/anthropic
MODEL=your-model
```

安全要求：

- 不要把 API Key 写入代码、README、提交记录或日志；
- 本地调试时使用当前 shell 的环境变量；
- 后续桌面端设置页需要接系统安全存储：Windows Credential Manager / macOS Keychain。

会后 Markdown 已升级为结构化纪要：

```text
摘要
决策
待办
风险
未解决问题
建议
原始转写
```

## Phase 4 当前说话人能力

当前已接入双轨 speaker 标记与手动重命名基础：

```text
mic track    → Me
system track → Remote
```

AI Service 已有 Diarization Provider 抽象：

```text
MockDiarizationProvider
FunAsrDiarizationProvider skeleton
PyannoteDiarizationProvider skeleton
```

已支持 API：

```text
GET   /api/meetings/{session_id}/speakers
PATCH /api/meetings/{session_id}/speakers/{speaker_id}
```

会后页面支持手动给 speaker 设置显示名。导出 Markdown 和会后转写会使用用户手动设置的显示名。

重要限制：

- 系统不会自动把 `Remote` / `Speaker 1` 猜成真实姓名；
- 只有用户手动重命名后才显示真实姓名；
- Windows system loopback 真实采集还未完成；
- 当前 system track 的 `Remote` 标记已在 AI Service 支持，可通过后续 Windows/macOS 系统音频采集接入真实音频帧。
## Phase 5 当前产品化能力

当前已补齐第一版试用所需的产品化入口：

```text
首页隐私确认
设置面板
最近会议列表
单条会议删除
全部会议数据删除
会议中 Debug 面板
Windows 打包脚本入口
```

设置面板支持：

```text
ASR Provider: mock / funasr
LLM Provider: mock / openai-compatible / anthropic
LLM Base URL
LLM Model
云端 LLM 开关
本地保存转写开关
Debug 日志文本开关
数据目录展示
API Key 是否已通过环境变量配置
```

安全边界：

- API Key 不会写入 SQLite，也不会显示在 UI 或 README 中；
- 当前只检测 `MEETING_COPILOT_LLM_API_KEY` 是否存在；
- 默认 `mock` LLM，不上传音频；
- 云端 LLM 只允许发送必要文本上下文，不发送原始音频；
- 删除全部会议数据会通过 SQLite 外键级联清理转写、建议、speaker 和快照。

### Phase 5 启动

```bash
corepack pnpm install
corepack pnpm dev:ai
corepack pnpm dev:desktop
```

浏览器开发模式：

```text
http://127.0.0.1:1420
```

### Phase 5 检查

```bash
corepack pnpm lint
corepack pnpm test
corepack pnpm build:desktop
```

Windows 打包入口：

```bash
corepack pnpm package:windows
```

打包需要本机 Rust、Tauri 和平台构建工具链可用；如果环境缺少 `cargo`，请先安装 Rust 工具链。
