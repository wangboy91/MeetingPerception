import json
from datetime import UTC, datetime
from typing import Any

from app.storage.database import connect, init_database


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class MeetingRepository:
    def create(
        self,
        meeting_id: str,
        title: str = "Untitled Meeting",
        mode: str = "general",
        user_role: str = "default",
    ) -> dict[str, Any]:
        init_database()
        now = utc_now()
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO meetings (
                    id, title, mode, user_role, status, started_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (meeting_id, title, mode, user_role, "recording", now, now, now),
            )
        return self.get(meeting_id) or {}

    def get(self, meeting_id: str) -> dict[str, Any] | None:
        init_database()
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM meetings WHERE id = ?",
                (meeting_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        init_database()
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM meetings
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def stop(self, meeting_id: str) -> dict[str, Any] | None:
        init_database()
        now = utc_now()
        with connect() as connection:
            connection.execute(
                """
                UPDATE meetings
                SET status = ?, ended_at = COALESCE(ended_at, ?), updated_at = ?
                WHERE id = ?
                """,
                ("stopped", now, now, meeting_id),
            )
        return self.get(meeting_id)

    def delete(self, meeting_id: str) -> bool:
        init_database()
        with connect() as connection:
            cursor = connection.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        return cursor.rowcount > 0

    def delete_all(self) -> int:
        init_database()
        with connect() as connection:
            cursor = connection.execute("DELETE FROM meetings")
        return cursor.rowcount


class TranscriptRepository:
    def create(self, meeting_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        init_database()
        created_at = payload.get("createdAt") or utc_now()
        transcript_id = payload["id"]
        segment_id = payload.get("segmentId") or transcript_id
        speaker_id = _speaker_db_id(
            meeting_id,
            payload.get("speakerId") or ("me" if payload["speaker"] == "Me" else "remote"),
        )
        speaker_label = payload["speaker"]
        track = payload.get("track") or ("mic" if speaker_label == "Me" else "system")
        SpeakerRepository().ensure(
            meeting_id=meeting_id,
            speaker_id=speaker_id,
            label=speaker_label,
            source=payload.get("speakerSource") or track,
        )
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO transcripts (
                    id, meeting_id, segment_id, speaker_label, track, text,
                    speaker_id, start_ms, end_ms, confidence, is_final, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transcript_id,
                    meeting_id,
                    segment_id,
                    speaker_label,
                    track,
                    payload["text"],
                    speaker_id,
                    int(payload.get("startMs") or 0),
                    int(payload.get("endMs") or 0),
                    payload.get("confidence"),
                    1 if payload.get("isFinal", True) else 0,
                    created_at,
                ),
            )
        return self.get(transcript_id) or {}

    def get(self, transcript_id: str) -> dict[str, Any] | None:
        init_database()
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM transcripts WHERE id = ?",
                (transcript_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_for_meeting(self, meeting_id: str) -> list[dict[str, Any]]:
        init_database()
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    transcripts.*,
                    COALESCE(speakers.display_name, transcripts.speaker_label) AS display_speaker_label
                FROM transcripts
                LEFT JOIN speakers
                    ON speakers.meeting_id = transcripts.meeting_id
                    AND speakers.id = transcripts.speaker_id
                WHERE transcripts.meeting_id = ?
                ORDER BY transcripts.start_ms ASC, transcripts.created_at ASC
                """,
                (meeting_id,),
            ).fetchall()
        return [dict(row) for row in rows]


class SuggestionRepository:
    def create(self, meeting_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        init_database()
        created_at = payload.get("createdAt") or utc_now()
        suggestion_id = payload["id"]
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO suggestions (
                    id, meeting_id, trigger_segment_id, title, problem_essence,
                    risk, suggested_reply, follow_up_question, action_item,
                    priority, raw_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    suggestion_id,
                    meeting_id,
                    payload.get("triggerSegmentId"),
                    payload["title"],
                    payload.get("problemEssence") or payload.get("rationale"),
                    payload.get("risk"),
                    payload.get("suggestedReply") or payload.get("recommendedResponse"),
                    payload.get("followUpQuestion"),
                    payload.get("actionItem"),
                    payload.get("priority", "medium"),
                    json.dumps(payload, ensure_ascii=False),
                    created_at,
                ),
            )
        return self.get(suggestion_id) or {}

    def get(self, suggestion_id: str) -> dict[str, Any] | None:
        init_database()
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM suggestions WHERE id = ?",
                (suggestion_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_for_meeting(self, meeting_id: str) -> list[dict[str, Any]]:
        init_database()
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM suggestions
                WHERE meeting_id = ?
                ORDER BY created_at ASC
                """,
                (meeting_id,),
            ).fetchall()
        return [dict(row) for row in rows]


class SpeakerRepository:
    def ensure(self, meeting_id: str, speaker_id: str, label: str, source: str) -> dict[str, Any]:
        init_database()
        speaker_id = _speaker_db_id(meeting_id, speaker_id)
        now = utc_now()
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO speakers (id, meeting_id, label, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    updated_at = excluded.updated_at
                """,
                (speaker_id, meeting_id, label, source, now, now),
            )
        return self.get(meeting_id, speaker_id) or {}

    def list_for_meeting(self, meeting_id: str) -> list[dict[str, Any]]:
        init_database()
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM speakers
                WHERE meeting_id = ?
                ORDER BY source ASC, label ASC
                """,
                (meeting_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, meeting_id: str, speaker_id: str) -> dict[str, Any] | None:
        init_database()
        speaker_id = _speaker_db_id(meeting_id, speaker_id)
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM speakers WHERE meeting_id = ? AND id = ?",
                (meeting_id, speaker_id),
            ).fetchone()
        return dict(row) if row else None

    def rename(self, meeting_id: str, speaker_id: str, display_name: str) -> dict[str, Any] | None:
        init_database()
        speaker_id = _speaker_db_id(meeting_id, speaker_id)
        now = utc_now()
        cleaned = display_name.strip()
        if not cleaned:
            cleaned = None
        with connect() as connection:
            connection.execute(
                """
                UPDATE speakers
                SET display_name = ?, updated_at = ?
                WHERE meeting_id = ? AND id = ?
                """,
                (cleaned, now, meeting_id, speaker_id),
            )
        return self.get(meeting_id, speaker_id)


def _speaker_db_id(meeting_id: str, speaker_id: str) -> str:
    prefix = f"{meeting_id}:"
    return speaker_id if speaker_id.startswith(prefix) else f"{prefix}{speaker_id}"


class SettingsRepository:
    def set(self, key: str, value: dict[str, Any]) -> None:
        init_database()
        now = utc_now()
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
                """,
                (key, json.dumps(value, ensure_ascii=False), now),
            )

    def get(self, key: str) -> dict[str, Any] | None:
        init_database()
        with connect() as connection:
            row = connection.execute(
                "SELECT value_json FROM settings WHERE key = ?",
                (key,),
            ).fetchone()
        return json.loads(row["value_json"]) if row else None
