# 09 前端交互与界面设计

## 1. 设计目标

这个产品不是后台系统，而是会议中使用的实时辅助工具。

前端设计原则：

- 安静；
- 信息密度适中；
- 不打断会议；
- 建议要短；
- 录音状态必须明显；
- 用户随时能暂停。

## 2. 页面结构

### 2.1 首页

功能：

- 新建会议；
- 选择会议模式；
- 选择用户角色；
- 选择音频设备；
- 配置 LLM；
- 查看隐私说明。

布局：

```text
顶部：产品名 + 设置
中间：开始会议卡片
底部：最近会议列表
```

首页字段：

```text
会议标题
会议模式
用户角色
麦克风设备
系统输出设备
是否保存记录
是否启用云端 LLM
```

### 2.2 会议中页面

推荐布局：

```text
┌───────────────────────────────────────────────┐
│ 录音中 ●  00:12:33     Mic: 正常  System: 正常 │
├─────────────────────────┬─────────────────────┤
│ 实时转写时间轴           │ 实时建议             │
│                         │                     │
│ [00:01] Me: ...         │ 建议卡片 1           │
│ [00:02] Remote: ...     │ 建议卡片 2           │
│                         │                     │
├─────────────────────────┴─────────────────────┤
│ 暂停  标记重点  静音建议  结束会议              │
└───────────────────────────────────────────────┘
```

### 2.3 会后页面

内容：

- 摘要；
- 决策；
- 待办；
- 风险；
- 未解决问题；
- 转写全文；
- 导出按钮。

## 3. 组件设计

### 3.1 RecordingStatus

显示：

- 录音状态；
- 会议时长；
- 麦克风状态；
- 系统音频状态；
- ASR 状态；
- LLM 状态。

状态：

```text
idle
starting
recording
paused
stopping
error
```

### 3.2 DeviceSelector

功能：

- 列出麦克风；
- 列出系统输出设备；
- 测试音量；
- 刷新设备。

### 3.3 TranscriptTimeline

显示：

```text
时间
说话人
内容
partial/final 状态
```

规则：

- 最新内容自动滚动；
- 用户手动滚动时暂停自动滚动；
- partial 用浅色；
- final 用正常色；
- Speaker 可重命名。

### 3.4 SuggestionPanel

建议卡片内容：

```text
标题
问题本质
建议回应
建议追问
待办
优先级
```

交互：

- 复制建议话术；
- 标记有用/无用；
- 忽略；
- 转为待办；
- 静音 5 分钟。

### 3.5 MeetingControls

按钮：

- 开始；
- 暂停；
- 恢复；
- 标记重点；
- 静音建议；
- 结束会议。

结束会议必须二次确认。

## 4. 状态管理

建议 store：

```ts
type MeetingState = {
  sessionId: string | null;
  status: 'idle' | 'starting' | 'recording' | 'paused' | 'stopping' | 'ended' | 'error';
  startedAt?: string;
  elapsedMs: number;
  transcripts: TranscriptItem[];
  suggestions: SuggestionItem[];
  audioStatus: AudioStatus;
};
```

## 5. WebSocket 处理

前端 `useMeetingSocket`：

职责：

- 连接；
- 重连；
- 分发消息；
- 更新 store；
- 显示错误。

伪代码：

```ts
switch (message.type) {
  case 'meeting.status':
    updateStatus(message.payload);
    break;
  case 'transcript.partial':
    updatePartialTranscript(message.payload);
    break;
  case 'transcript.final':
    appendFinalTranscript(message.payload);
    break;
  case 'suggestion.created':
    appendSuggestion(message.payload);
    break;
  case 'error':
    showError(message.payload);
    break;
}
```

## 6. 用户设置

设置项：

```text
ASR Provider
LLM Provider
Base URL
Model
API Key
是否启用云端 LLM
是否保存会议记录
是否允许 debug 日志
默认会议模式
默认用户角色
```

API Key 保存：

- 不要放在普通文本配置；
- 使用系统安全存储；
- MVP 可先本地加密文件，但要留下接口。

## 7. 隐私提示

开始会议前显示：

```text
请确保你有权记录当前会议内容。默认情况下，音频不会上传云端；如启用云端模型，系统会将必要的文字上下文发送给模型服务。
```

会议中必须显示：

```text
录音中
```

不能隐藏。

## 8. 颜色和视觉

MVP 不追求复杂视觉。

推荐：

- 背景：浅灰/白；
- 录音状态：醒目红点；
- 高优先级建议：明确标识；
- 转写区域：阅读优先；
- 建议区域：卡片式。

## 9. 空状态

### 9.1 无音频

```text
未检测到声音，请检查麦克风或系统音量。
```

### 9.2 未配置 LLM

```text
已开启转写。配置模型后可获得实时建议。
```

### 9.3 ASR 未就绪

```text
正在加载语音识别模型，首次启动可能较慢。
```

## 10. 验收标准

- 首页能创建会议；
- 会议页能显示 mock transcript；
- WebSocket 断开能提示并重连；
- 建议卡片能展示；
- 可以暂停/恢复；
- 可以结束会议并进入会后页；
- 可以导出 Markdown。
