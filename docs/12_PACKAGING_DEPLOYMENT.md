# 12 打包、部署与发布

## 1. 目标

第一版做本地桌面应用，用户下载安装后即可使用。

优先平台：

```text
Windows 10/11
```

后续平台：

```text
macOS
Linux
```

## 2. 本地开发启动

建议根目录脚本：

```bash
pnpm dev
```

内部启动：

```text
启动 Python AI Service
启动 Tauri Desktop
连接 WebSocket
```

## 3. Python 服务发布方式

### 3.1 开发期

直接运行：

```bash
cd services/ai-service
uv run fastapi dev app/main.py --port 8765
```

### 3.2 桌面打包期

有两种方式：

#### 方式 A：打包 Python 可执行文件

用 PyInstaller/Nuitka 把 AI service 打包成本地可执行。

优点：

- 用户不用安装 Python；
- 桌面端可以启动子进程。

缺点：

- 包体积较大；
- 模型文件管理复杂。

#### 方式 B：要求用户安装本地服务

优点：

- 打包简单；
- 适合开发者用户。

缺点：

- 普通用户门槛高。

MVP 面向自己和技术用户时，可以先用方式 B。

产品化时必须做方式 A。

## 4. 模型文件管理

不要把大型模型直接提交到 Git。

建议：

```text
models/
├── asr/
├── vad/
└── diarization/
```

第一次启动时：

- 检查模型是否存在；
- 不存在则提示下载；
- 显示下载进度；
- 支持手动指定模型路径。

## 5. 配置路径

Windows：

```text
%APPDATA%/MeetingCopilot/config.json
%APPDATA%/MeetingCopilot/data/meetings.db
%APPDATA%/MeetingCopilot/logs/
%APPDATA%/MeetingCopilot/models/
```

macOS：

```text
~/Library/Application Support/MeetingCopilot/
```

Linux：

```text
~/.config/meeting-copilot/
```

## 6. 打包命令

Tauri：

```bash
pnpm tauri build
```

Rust：

```bash
cargo build --release
```

Python 服务：

```bash
pyinstaller services/ai-service/app/main.py
```

后续要写统一脚本：

```bash
scripts/build-windows.ps1
scripts/build-macos.sh
scripts/build-linux.sh
```

## 7. 自动更新

MVP 不做自动更新。

后续使用 Tauri updater。

## 8. 发布包内容

Windows 发布包：

```text
MeetingCopilot.exe
ai-service.exe
default config
model downloader
license
privacy notice
```

不建议第一版内置大型 ASR 模型。

可以提供：

- tiny/small 模型内置；
- full 模型首次启动下载。

## 9. 版本规划

### v0.1.0 Dev

- mock ASR；
- mock LLM；
- UI 闭环。

### v0.2.0 Local ASR

- 麦克风采集；
- FunASR；
- SQLite；
- 导出 Markdown。

### v0.3.0 System Audio

- Windows 系统输出采集；
- mic/system 双轨；
- 实时建议。

### v0.4.0 Diarization

- Speaker 1/2/3；
- speaker 重命名；
- 会后纪要增强。

### v1.0.0 MVP

- Windows 可安装；
- 本地隐私配置；
- ASR/LLM 可配置；
- 稳定 60 分钟会议。

## 10. 验收标准

- 开发环境一条命令可启动；
- Windows 可以打包；
- 用户无需手动启动多个服务；
- 配置和数据保存到用户目录；
- 模型缺失时有明确提示；
- 卸载不会误删用户主动导出的文件。
