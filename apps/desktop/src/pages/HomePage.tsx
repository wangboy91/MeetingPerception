import { AssistantRole, MeetingSession } from "@meeting-copilot/shared";
import { useEffect, useState } from "react";

import { RecentMeetings } from "../components/RecentMeetings";
import { SettingsPanel } from "../components/SettingsPanel";
import { useAudioDevices } from "../hooks/useAudioDevices";
import { ASSISTANT_ROLE_OPTIONS } from "../services/assistantRoles";
import {
  AppSettings,
  createMeeting,
  deleteAllMeetings,
  deleteMeeting,
  getSettings,
  listMeetings,
  saveSettings,
} from "../services/aiServiceClient";

interface HomePageProps {
  assistantRole: AssistantRole;
  micDeviceId: string;
  onMicDeviceChange: (deviceId: string) => void;
  onOpenSummary: (sessionId: string) => void;
  onRoleChange: (role: AssistantRole) => void;
  onStart: (sessionId: string) => void;
}

export function HomePage({
  assistantRole,
  micDeviceId,
  onMicDeviceChange,
  onOpenSummary,
  onRoleChange,
  onStart,
}: HomePageProps) {
  const { micDevices, error, requestPermissionAndRefresh } = useAudioDevices();
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [recentMeetings, setRecentMeetings] = useState<MeetingSession[]>([]);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    void loadHomeData();
  }, []);

  async function loadHomeData() {
    try {
      const [nextSettings, meetings] = await Promise.all([getSettings(), listMeetings()]);
      setSettings(nextSettings);
      setRecentMeetings(meetings);
      setStatusText(null);
    } catch {
      setStatusText("无法连接 AI Service，请先启动本地服务。");
    }
  }

  async function handleStart() {
    if (!privacyAccepted) {
      setStartError("开始前需要确认你有权记录当前会议。");
      return;
    }

    try {
      const meeting = await createMeeting(assistantRole);
      onStart(meeting.id);
    } catch {
      setStartError("创建会议失败，请确认 AI Service 正在运行。");
    }
  }

  async function handleSaveSettings() {
    if (!settings) {
      return;
    }
    try {
      const nextSettings = await saveSettings(settings);
      setSettings(nextSettings);
      setStatusText("设置已保存。Provider 运行时切换将在后续服务重载中完善。");
    } catch {
      setStatusText("保存设置失败，请确认 AI Service 正在运行。");
    }
  }

  async function handleDeleteMeeting(sessionId: string) {
    if (!window.confirm("确认删除这条会议记录？删除后不能在 UI 中恢复。")) {
      return;
    }
    await deleteMeeting(sessionId);
    await loadHomeData();
  }

  async function handleDeleteAllMeetings() {
    if (!window.confirm("确认删除全部会议记录？转写、建议和 speaker 设置都会一起删除。")) {
      return;
    }
    const deleted = await deleteAllMeetings();
    await loadHomeData();
    setStatusText(`已删除 ${deleted} 条会议记录。`);
  }

  return (
    <main className="home-layout">
      <section className="home-panel">
        <p className="eyebrow">Local-first Meeting Copilot</p>
        <h1>Meeting Copilot Local</h1>
        <p className="intro">
          实时监听会议音频、展示转写，并在关键风险、问题、决策和待办出现时给出简短建议。
        </p>

        <div className="setup-grid" aria-label="会议启动设置">
          <label>
            麦克风
            <select value={micDeviceId} onChange={(event) => onMicDeviceChange(event.target.value)}>
              <option value="default">默认麦克风</option>
              {micDevices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.isDefault ? `${device.label}（默认）` : device.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            系统输出
            <select defaultValue="system-output">
              <option value="system-output">默认系统输出（接口预留）</option>
            </select>
          </label>
          <label>
            助手角色
            <select
              value={assistantRole}
              onChange={(event) => onRoleChange(event.target.value as AssistantRole)}
            >
              {ASSISTANT_ROLE_OPTIONS.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <p className="role-hint">
          当前角色：{ASSISTANT_ROLE_OPTIONS.find((role) => role.id === assistantRole)?.description}
        </p>
        <p className="privacy-note">
          默认本地优先；麦克风音频会转为 16k mono PCM 后发送到本机 AI Service。
        </p>
        <label className="checkbox-row privacy-confirm">
          <input
            type="checkbox"
            checked={privacyAccepted}
            onChange={(event) => {
              setPrivacyAccepted(event.target.checked);
              setStartError(null);
            }}
          />
          <span>我确认有权记录当前会议，并已遵守所在地、组织和参会方的相关要求。</span>
        </label>
        {error ? <p className="device-error">{error}</p> : null}
        {startError ? <p className="device-error">{startError}</p> : null}
        <button className="secondary-action" type="button" onClick={requestPermissionAndRefresh}>
          授权并刷新麦克风
        </button>
        <button
          className="primary-action"
          type="button"
          onClick={handleStart}
          disabled={!privacyAccepted}
        >
          开始会议
        </button>
      </section>

      <div className="home-secondary-grid">
        <SettingsPanel
          settings={settings}
          statusText={statusText}
          onChange={setSettings}
          onSave={handleSaveSettings}
          onDeleteAll={handleDeleteAllMeetings}
        />
        <RecentMeetings
          meetings={recentMeetings}
          onOpen={onOpenSummary}
          onDelete={handleDeleteMeeting}
        />
      </div>
    </main>
  );
}
