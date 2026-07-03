CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    mode TEXT NOT NULL,
    user_role TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transcripts (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    speaker_id TEXT,
    speaker_label TEXT NOT NULL,
    track TEXT NOT NULL,
    text TEXT NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    confidence REAL,
    is_final INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS suggestions (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    trigger_segment_id TEXT,
    title TEXT NOT NULL,
    problem_essence TEXT,
    risk TEXT,
    suggested_reply TEXT,
    follow_up_question TEXT,
    action_item TEXT,
    priority TEXT NOT NULL,
    raw_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS speakers (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    label TEXT NOT NULL,
    source TEXT NOT NULL,
    display_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meeting_state_snapshots (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    current_topic TEXT,
    summary TEXT,
    decisions_json TEXT,
    risks_json TEXT,
    todos_json TEXT,
    open_questions_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transcripts_meeting_id_created_at
    ON transcripts(meeting_id, created_at);

CREATE INDEX IF NOT EXISTS idx_suggestions_meeting_id_created_at
    ON suggestions(meeting_id, created_at);
