interface MeetingControlsProps {
  onEnd: () => void;
}

export function MeetingControls({ onEnd }: MeetingControlsProps) {
  return (
    <div className="meeting-controls">
      <button type="button" disabled>
        暂停
      </button>
      <button type="button" disabled>
        静音建议
      </button>
      <button className="danger-action" type="button" onClick={onEnd}>
        结束会议
      </button>
    </div>
  );
}
