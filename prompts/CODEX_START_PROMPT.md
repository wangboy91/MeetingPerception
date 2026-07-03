# Codex 启动提示词

你现在要开发一个桌面端 Meeting Copilot 软件。

请先阅读以下文件：

1. `AGENTS.md`
2. `README.md`
3. `docs/00_PROJECT_OVERVIEW.md`
4. `docs/01_PRD.md`
5. `docs/02_ARCHITECTURE.md`
6. `docs/04_REPO_STRUCTURE.md`
7. 当前阶段任务文件，例如 `tasks/PHASE_0_BOOTSTRAP.md`

请严格按工程化方式开发，不要写一次性 demo。

当前阶段任务：

```text
先完成 Phase 0：项目骨架搭建。
```

要求：

- 先建立 monorepo；
- Tauri + React + TypeScript 桌面端能启动；
- Python FastAPI AI Service 能启动；
- WebSocket 能推送 mock transcript；
- 前端能展示 mock transcript；
- 不要先实现真实音频采集；
- 每个模块预留接口；
- 完成后告诉我如何启动、如何测试、当前限制和下一步。
