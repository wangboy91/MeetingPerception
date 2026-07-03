import { useState } from "react";
import { AssistantRole } from "@meeting-copilot/shared";

import { HomePage } from "../pages/HomePage";
import { MeetingPage } from "../pages/MeetingPage";
import { SummaryPage } from "../pages/SummaryPage";

export function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [summarySessionId, setSummarySessionId] = useState<string | null>(null);
  const [assistantRole, setAssistantRole] = useState<AssistantRole>("tech-review");
  const [micDeviceId, setMicDeviceId] = useState<string>("default");

  if (sessionId) {
    return (
      <MeetingPage
        sessionId={sessionId}
        assistantRole={assistantRole}
        micDeviceId={micDeviceId}
        onRoleChange={setAssistantRole}
        onEnd={() => {
          setSummarySessionId(sessionId);
          setSessionId(null);
        }}
      />
    );
  }

  if (summarySessionId) {
    return (
      <SummaryPage
        sessionId={summarySessionId}
        onBackHome={() => setSummarySessionId(null)}
      />
    );
  }

  return (
    <HomePage
      assistantRole={assistantRole}
      micDeviceId={micDeviceId}
      onMicDeviceChange={setMicDeviceId}
      onOpenSummary={setSummarySessionId}
      onRoleChange={setAssistantRole}
      onStart={setSessionId}
    />
  );
}
