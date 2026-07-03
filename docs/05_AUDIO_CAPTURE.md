# 05 音频采集设计

## 1. 目标

采集两路音频：

```text
mic track：本地麦克风输入
system track：电脑系统输出声音
```

这样可以覆盖：

- 本地会议；
- 远程会议；
- 浏览器会议；
- Zoom/Teams/飞书/腾讯会议等桌面软件。

## 2. 本质问题

电脑会议声音分两类：

```text
自己说的话：来自麦克风
别人说的话：来自电脑扬声器/耳机输出
```

所以第一版不要试图直接解析会议软件。

应该先做：

```text
采集麦克风 + 采集系统输出
```

这样软件与会议平台解耦。

## 3. MVP 支持范围

第一阶段优先：

```text
Windows 10/11
麦克风采集
系统输出 loopback 采集
```

后续扩展：

```text
macOS：ScreenCaptureKit / CoreAudio / BlackHole 虚拟音频
Linux：PipeWire / PulseAudio monitor source
```

## 4. 音频帧格式

所有音频统一转换为：

```text
sample_rate: 16000 Hz
channels: 1
format: PCM signed 16-bit little endian
frame_duration: 20ms / 40ms / 100ms 可配置
track: mic | system
```

音频帧结构：

```json
{
  "session_id": "uuid",
  "track": "mic",
  "timestamp_ms": 123456,
  "sample_rate": 16000,
  "channels": 1,
  "format": "pcm_s16le",
  "seq": 1001,
  "data": "binary"
}
```

## 5. 采集策略

### 5.1 麦克风输入

流程：

```text
枚举输入设备
→ 用户选择设备
→ 打开 stream
→ 重采样到 16k mono
→ 推送 AudioFrame
```

### 5.2 系统输出

Windows 采用 loopback capture。

流程：

```text
枚举输出设备
→ 用户选择当前播放设备
→ 打开 loopback stream
→ 重采样到 16k mono
→ 推送 AudioFrame(track=system)
```

macOS 系统输出采集分两种路线：

```text
ScreenCaptureKit 系统音频捕获
或 BlackHole / Loopback 等虚拟音频设备
→ 重采样到 16k mono
→ 推送 AudioFrame(track=system)
```

优先策略：

- Windows：优先 WASAPI loopback；
- macOS：优先 ScreenCaptureKit，若权限或系统版本约束较重，再支持虚拟音频设备方案；
- 两个平台都必须保留 mic/system 双轨，不在采集层混音。

### 5.3 双轨同步

不要在采集层强行合并 mic 和 system。

保留双轨：

```text
mic track 独立进入 AI service
system track 独立进入 AI service
```

原因：

- 更容易区分“我”和“别人”；
- 更方便后续降噪；
- 更方便后续说话人分离；
- 更方便调试。

## 6. 回声问题

如果用户外放开会，麦克风可能录到远程声音，system track 也会录到远程声音，导致重复。

MVP 处理策略：

- UI 提醒用户优先使用耳机；
- 简单能量检测去重；
- 如果 mic 和 system 文本高度相似，优先保留 system；
- 后续再做 AEC 回声消除。

第一版不要过早实现复杂 AEC。

## 7. Rust 接口设计

建议抽象：

```rust
pub enum AudioTrack {
    Mic,
    System,
}

pub struct AudioDevice {
    pub id: String,
    pub name: String,
    pub is_default: bool,
    pub track_type: AudioTrack,
}

pub struct AudioFrame {
    pub session_id: String,
    pub track: AudioTrack,
    pub timestamp_ms: u64,
    pub sample_rate: u32,
    pub channels: u16,
    pub seq: u64,
    pub data: Vec<i16>,
}

pub trait AudioCapture {
    fn list_devices(&self) -> Result<Vec<AudioDevice>>;
    fn start(&mut self, config: CaptureConfig) -> Result<()>;
    fn stop(&mut self) -> Result<()>;
}
```

## 8. Tauri Commands

建议命令：

```rust
#[tauri::command]
async fn list_audio_devices() -> Result<Vec<AudioDeviceDto>, String>

#[tauri::command]
async fn start_audio_capture(config: CaptureConfigDto) -> Result<(), String>

#[tauri::command]
async fn stop_audio_capture() -> Result<(), String>
```

## 9. 推送到 AI Service

两种方案：

### 方案 A：Tauri 采集后 WebSocket 推给 Python

优点：

- 边界清晰；
- Python 服务独立；
- 容易调试。

缺点：

- 本地 WebSocket binary frame 需要处理好。

### 方案 B：Python 直接采集音频

优点：

- 快速 demo；
- Python 库多。

缺点：

- 系统音频 loopback 跨平台麻烦；
- 长期不如 Rust 工程化。

MVP 建议：

```text
阶段 1 可先 Python 采 mic 或 mock audio
阶段 2 用 Rust 做正式音频采集
```

## 10. 权限提示

UI 必须提示：

- 当前正在监听麦克风；
- 当前正在监听系统声音；
- 是否保存会议记录；
- 是否允许发送文本到云端 LLM。

## 11. 错误处理

| 错误 | UI 提示 |
|---|---|
| 无麦克风权限 | 请在系统设置中允许麦克风访问 |
| 设备被占用 | 当前设备可能被其他应用独占 |
| 系统输出采集失败 | 可先只监听麦克风，或切换输出设备 |
| 音频服务启动失败 | 请重启应用或检查权限 |
| 无音频输入 | 未检测到声音，请检查设备或音量 |

## 12. 验收标准

第一阶段验收：

- 能列出麦克风设备；
- 能采集麦克风音频；
- 能将音频帧发送给 AI Service；
- AI Service 能收到 frame 并打印音量/VAD 状态；
- UI 能显示当前输入音量；
- 采集 10 分钟不崩溃。

第二阶段验收：

- Windows 能采集系统输出；
- mic/system 双轨可同时采集；
- UI 能分别显示两路状态；
- 双轨音频都能进入 ASR。
