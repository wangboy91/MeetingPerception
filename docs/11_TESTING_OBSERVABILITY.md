# 11 测试与可观测性

## 1. 测试目标

这个项目最容易失败的地方不是 UI，而是实时链路不稳定。

测试重点：

- 音频是否稳定采集；
- ASR 是否可用；
- WebSocket 是否稳定；
- LLM 是否不会阻塞转写；
- 数据是否正确保存；
- 长会议是否内存稳定。

## 2. 测试分层

```text
Unit Test
Integration Test
E2E Test
Manual Audio Test
Performance Test
```

## 3. Python 服务测试

### 3.1 单元测试

覆盖：

- VAD provider；
- ASR mock provider；
- transcript processor；
- event detector；
- LLM JSON parser；
- repository。

示例：

```python
def test_event_detector_detects_question():
    text = "这个需求下周上线会不会影响支付流程？"
    event = detector.detect(text)
    assert event.should_suggest is True
    assert event.event_type in ["question", "risk"]
```

### 3.2 集成测试

覆盖：

- 创建会议；
- 推送 mock transcript；
- 写入数据库；
- 触发建议；
- WebSocket 收到消息。

## 4. 前端测试

覆盖：

- 首页表单；
- 会议状态切换；
- TranscriptTimeline 渲染；
- SuggestionPanel 渲染；
- WebSocket 消息分发。

建议：

```text
Vitest
React Testing Library
Playwright 后续补充
```

## 5. Rust 测试

覆盖：

- 设备枚举；
- 音频帧格式转换；
- 重采样；
- mock capture。

真实设备采集需要手动测试，不强求 CI。

## 6. 手动测试用例

### 6.1 麦克风测试

步骤：

1. 启动 App；
2. 选择麦克风；
3. 点击开始会议；
4. 对着麦克风说话 30 秒；
5. 检查是否出现字幕。

通过标准：

- 音量条有变化；
- VAD 状态变化；
- 出现转写；
- 数据库有记录。

### 6.2 系统音频测试

步骤：

1. 播放一段中文音频；
2. 开启系统输出监听；
3. 检查是否转写。

通过标准：

- system track 有音量；
- speaker 显示 Remote；
- 文字进入时间轴。

### 6.3 长会议测试

步骤：

1. 运行 60 分钟模拟音频；
2. 观察 CPU/内存；
3. 检查 DB 大小；
4. 检查 UI 是否卡顿。

通过标准：

- 无崩溃；
- 内存不持续无限增长；
- WebSocket 不断开；
- 会议结束可生成摘要。

## 7. 性能指标

| 指标 | 目标 |
|---|---|
| ASR 首句延迟 | 1～3 秒 |
| 建议生成延迟 | 3～8 秒 |
| WebSocket 推送延迟 | < 200ms |
| 30 分钟会议内存增长 | 可控，无明显泄漏 |
| UI FPS | 不明显卡顿 |

## 8. 可观测性

### 8.1 日志字段

```json
{
  "timestamp": "...",
  "level": "info",
  "session_id": "uuid",
  "module": "asr",
  "event": "segment_transcribed",
  "duration_ms": 1200,
  "success": true
}
```

不要默认记录完整会议文本。

### 8.2 指标

建议记录：

- 音频帧数量；
- VAD speech ratio；
- ASR 调用次数；
- ASR 平均耗时；
- LLM 调用次数；
- LLM 平均耗时；
- WebSocket 重连次数；
- DB 写入错误次数。

### 8.3 Debug 面板

开发模式可以提供：

```text
当前音频设备
音量
VAD 状态
ASR 状态
LLM 状态
WebSocket 状态
最近错误
```

## 9. CI 建议

GitHub Actions：

```text
frontend lint/test
python lint/test
rust fmt/clippy/test
```

不要在 CI 中强依赖真实音频设备和大型模型。

## 10. 验收标准

- 至少有 mock 全链路测试；
- 单元测试覆盖关键处理器；
- 有手动测试文档；
- 有基础日志；
- 长会议不明显内存泄漏；
- LLM 失败不影响 ASR。
