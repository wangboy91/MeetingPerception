# Phase 4：系统音频与说话人分离

## 目标

实现更接近真实会议的能力：

```text
Mic Track → Me
System Track → Remote / Speaker 1 / Speaker 2
```

## 输入文档

- `docs/05_AUDIO_CAPTURE.md`
- `docs/06_ASR_DIARIZATION.md`

## 任务清单

### 1. Windows 系统输出采集

实现 system track。

要求：

- 能采集电脑正在播放的声音；
- 转成 16k mono；
- 与 mic track 分开；
- UI 显示 system 音量。

### 2. 双轨处理

AI Service 支持：

```text
track = mic
track = system
```

mic 默认 speaker = Me。

system 默认 speaker = Remote。

### 3. Speaker Diarization 接口

实现：

- DiarizationProvider base；
- MockDiarizationProvider；
- FunASR/Pyannote Provider skeleton。

### 4. Speaker 重命名

UI 支持：

```text
Speaker 1 → 张三
Speaker 2 → 李四
```

注意：

- 用户手动命名才显示真实名字；
- 系统不能自动猜真实姓名。

### 5. 去重策略

处理外放导致 mic/system 重复：

- 文本相似度检测；
- 时间重叠检测；
- 优先保留 system。

## 验收标准

- Windows 可采集系统输出；
- mic/system 能同时转写；
- UI 能区分 Me 和 Remote；
- Speaker 重命名可保存；
- 会后导出使用用户重命名 label。
