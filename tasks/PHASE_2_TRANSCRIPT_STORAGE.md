# Phase 2：转写流、本地存储与导出

## 目标

让会议记录可以沉淀下来。

```text
Transcript → SQLite → 会后页面 → Markdown 导出
```

## 输入文档

- `docs/08_API_AND_DATA_MODEL.md`
- `docs/09_FRONTEND_UX.md`
- `docs/10_SECURITY_PRIVACY.md`

## 任务清单

### 1. SQLite 初始化

实现表：

- meetings；
- transcripts；
- suggestions；
- speakers；
- meeting_state_snapshots；
- settings。

### 2. Repository 层

实现：

- MeetingRepository；
- TranscriptRepository；
- SuggestionRepository；
- SettingsRepository。

### 3. API 完善

实现：

- 获取会议详情；
- 获取转写；
- 获取建议；
- 删除会议；
- 导出 Markdown。

### 4. 会后页面

展示：

- 会议标题；
- 开始/结束时间；
- 原始转写；
- 导出按钮。

### 5. Markdown 导出

格式参考 `docs/08_API_AND_DATA_MODEL.md`。

## 验收标准

- 创建会议会写入 DB；
- transcript.final 会写入 DB；
- 结束会议后能看到历史记录；
- 可以导出 Markdown；
- 删除会议可用；
- 默认不保存原始音频。
