import { useCallback, useEffect, useState } from "react";

export interface AudioInputDevice {
  id: string;
  label: string;
  isDefault: boolean;
}

export function useAudioDevices() {
  const [micDevices, setMicDevices] = useState<AudioInputDevice[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!navigator.mediaDevices?.enumerateDevices) {
      setError("当前运行环境不支持音频设备枚举");
      return;
    }

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs = devices
        .filter((device) => device.kind === "audioinput")
        .map((device, index) => ({
          id: device.deviceId,
          label: device.label || `麦克风 ${index + 1}`,
          isDefault: device.deviceId === "default" || index === 0,
        }));

      setMicDevices(inputs);
      setError(null);
    } catch {
      setError("无法枚举麦克风设备，请检查浏览器或系统权限");
    }
  }, []);

  const requestPermissionAndRefresh = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      await refresh();
    } catch {
      setError("未获得麦克风权限，会议中将无法采集真实音频");
    }
  }, [refresh]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { micDevices, error, refresh, requestPermissionAndRefresh };
}
