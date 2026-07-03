# Phase 5：产品化与发布

## 目标

把开发版变成可以给真实用户试用的 MVP。

## 输入文档

- `docs/09_FRONTEND_UX.md`
- `docs/10_SECURITY_PRIVACY.md`
- `docs/11_TESTING_OBSERVABILITY.md`
- `docs/12_PACKAGING_DEPLOYMENT.md`

## 任务清单

### 1. 设置页完善

支持：

- ASR Provider 配置；
- LLM Provider 配置；
- API Key 配置；
- 隐私选项；
- 数据目录；
- 删除全部数据。

### 2. 错误体验

完善：

- 麦克风权限错误；
- 系统音频采集失败；
- ASR 模型缺失；
- LLM API Key 缺失；
- 网络错误；
- DB 写入失败。

### 3. Debug 面板

开发模式显示：

- audio frame count；
- VAD 状态；
- ASR 状态；
- LLM 调用次数；
- WebSocket 状态；
- 最近错误。

### 4. 隐私提示

实现：

- 开始会议前授权提示；
- 会议中录音状态；
- 云端 LLM 开关说明；
- 删除记录。

### 5. 打包

实现 Windows 打包脚本。

### 6. 测试

完成：

- 30 分钟真实会议测试；
- 60 分钟模拟音频测试；
- LLM 失败测试；
- ASR 失败测试；
- WebSocket 断线重连测试。

## 验收标准

- Windows 可以安装/启动；
- 普通用户不用手动启动后端；
- 60 分钟会议不崩溃；
- 默认不上传音频；
- 可以导出 Markdown；
- 可以删除会议记录；
- 有清晰 README。
