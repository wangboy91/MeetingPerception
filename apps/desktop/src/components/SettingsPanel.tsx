import { AppSettings } from "../services/aiServiceClient";

interface SettingsPanelProps {
  settings: AppSettings | null;
  statusText: string | null;
  onChange: (settings: AppSettings) => void;
  onSave: () => void;
  onDeleteAll: () => void;
}

export function SettingsPanel({
  settings,
  statusText,
  onChange,
  onSave,
  onDeleteAll,
}: SettingsPanelProps) {
  if (!settings) {
    return (
      <section className="settings-panel">
        <div className="section-heading">
          <h2>设置</h2>
          <span>加载中</span>
        </div>
      </section>
    );
  }

  const update = <TKey extends keyof AppSettings>(key: TKey, value: AppSettings[TKey]) => {
    onChange({ ...settings, [key]: value });
  };

  return (
    <section className="settings-panel">
      <div className="section-heading">
        <h2>设置</h2>
        <span>{settings.cloudLlmEnabled ? "云端 LLM 已开启" : "本地优先"}</span>
      </div>

      <div className="settings-grid">
        <label>
          ASR Provider
          <select
            value={settings.asrProvider}
            onChange={(event) => update("asrProvider", event.target.value as AppSettings["asrProvider"])}
          >
            <option value="mock">Mock ASR</option>
            <option value="funasr">FunASR</option>
          </select>
        </label>

        <label>
          Diarization Provider
          <select
            value={settings.diarizationProvider}
            onChange={(event) =>
              update("diarizationProvider", event.target.value as AppSettings["diarizationProvider"])
            }
          >
            <option value="mock">Track-based Mock</option>
            <option value="funasr">FunASR speaker</option>
            <option value="pyannote">Pyannote</option>
          </select>
        </label>

        <label>
          LLM Provider
          <select
            value={settings.llmProvider}
            onChange={(event) => update("llmProvider", event.target.value as AppSettings["llmProvider"])}
          >
            <option value="mock">Mock</option>
            <option value="openai-compatible">OpenAI-compatible</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </label>

        <label>
          Model
          <input
            value={settings.llmModel}
            placeholder="mock"
            onChange={(event) => update("llmModel", event.target.value)}
          />
        </label>

        <label className="wide-field">
          Base URL
          <input
            value={settings.llmBaseUrl}
            placeholder="通过环境变量或这里填写"
            onChange={(event) => update("llmBaseUrl", event.target.value)}
          />
        </label>
      </div>

      <div className="settings-toggles">
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={settings.cloudLlmEnabled}
            disabled={!settings.apiKeyConfigured && settings.llmProvider !== "mock"}
            onChange={(event) => update("cloudLlmEnabled", event.target.checked)}
          />
          <span>允许云端 LLM 处理必要文本上下文，不上传音频</span>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={settings.storeTranscript}
            onChange={(event) => update("storeTranscript", event.target.checked)}
          />
          <span>本地保存转写和建议</span>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={settings.debugLogTranscript}
            onChange={(event) => update("debugLogTranscript", event.target.checked)}
          />
          <span>Debug 日志允许记录会议文本片段</span>
        </label>
      </div>

      <p className="settings-note">
        API Key 不会写入数据库。当前状态：
        {settings.apiKeyConfigured ? "已从环境变量读取" : "未配置 MEETING_COPILOT_LLM_API_KEY"}。
      </p>
      <p className="settings-note">
        FunASR/Pyannote 需要本地安装对应 Python 依赖和模型；缺失时会自动回退到 Track-based Mock。
      </p>
      <p className="settings-note">数据目录：{settings.dataDir}</p>
      {statusText ? <p className="settings-note">{statusText}</p> : null}

      <div className="settings-actions">
        <button className="secondary-action" type="button" onClick={onSave}>
          保存设置
        </button>
        <button className="danger-action" type="button" onClick={onDeleteAll}>
          删除全部会议数据
        </button>
      </div>
    </section>
  );
}
