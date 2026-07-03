# Phase 0：项目骨架搭建

## 目标

建立可运行的 monorepo 工程骨架，让后续每个模块都能独立开发和测试。

## 输入文档

Codex 开始前必须阅读：

- `AGENTS.md`
- `README.md`
- `docs/00_PROJECT_OVERVIEW.md`
- `docs/02_ARCHITECTURE.md`
- `docs/04_REPO_STRUCTURE.md`

## 任务清单

### 1. 创建 monorepo

创建目录：

```text
apps/desktop
crates/audio-capture
services/ai-service
packages/shared
scripts
```

### 2. 初始化桌面端

技术：

```text
Tauri + React + TypeScript
```

要求：

- TypeScript strict；
- 基础页面可启动；
- 有 HomePage 和 MeetingPage；
- 有基础路由或状态切换；
- 有基础样式。

### 3. 初始化 Python AI Service

技术：

```text
FastAPI + WebSocket + Pydantic
```

要求：

- `GET /health` 可用；
- `POST /api/meetings` 可用；
- WebSocket `/ws/meetings/{session_id}` 可连接；
- 每 2 秒推送一条 mock transcript。

### 4. 初始化共享类型

在 `packages/shared` 定义：

- WebSocket message type；
- Transcript type；
- Suggestion type；
- Meeting status type。

### 5. 初始化脚本

根目录提供：

```bash
pnpm dev:desktop
pnpm dev:ai
pnpm lint
pnpm test
```

## 验收标准

- 根目录 README 有启动说明；
- AI Service 可以单独启动；
- Desktop 可以单独启动；
- Desktop 能连上 AI Service WebSocket；
- UI 能展示 mock transcript；
- 没有真实 ASR 也能跑通。

## Codex 执行提示词

```text
请按 tasks/PHASE_0_BOOTSTRAP.md 完成项目骨架。
优先保证工程能启动，不要实现真实音频采集。
完成后输出改动文件、启动方式、测试方式和已知限制。
```
