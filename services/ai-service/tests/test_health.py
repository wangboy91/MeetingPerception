from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-service"}


def test_meeting_storage_and_markdown_export(monkeypatch) -> None:
    db_path = Path("services/ai-service/data") / f"test-{uuid4()}.sqlite3"
    monkeypatch.setenv("MEETING_COPILOT_DB_PATH", str(db_path))
    client = TestClient(app)

    create_response = client.post(
        "/api/meetings",
        json={"title": "需求评审", "mode": "technical_review", "userRole": "backend_engineer"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    with client.websocket_connect(f"/ws/meetings/{session_id}") as websocket:
        websocket.receive_json()
        for seq in range(13):
            websocket.send_json(_audio_frame(seq=seq, rms=0.05, session_id=session_id))
            websocket.receive_json()
        saw_suggestion = False
        for seq in range(13, 24):
            websocket.send_json(_audio_frame(seq=seq, rms=0.0, session_id=session_id))
            message = websocket.receive_json()
            if message["type"] == "transcript.final":
                continue
            if message["type"] == "analysis.event":
                continue
            if message["type"] == "suggestion.created":
                saw_suggestion = True
                break
        else:
            raise AssertionError("expected suggestion.created to be persisted")
    assert saw_suggestion is True

    transcripts_response = client.get(f"/api/meetings/{session_id}/transcripts")
    assert transcripts_response.status_code == 200
    transcripts = transcripts_response.json()
    assert len(transcripts) == 1
    assert transcripts[0]["meeting_id"] == session_id

    speakers_response = client.get(f"/api/meetings/{session_id}/speakers")
    assert speakers_response.status_code == 200
    speakers = speakers_response.json()
    assert speakers[0]["label"] == "Me"
    rename_response = client.patch(
        f"/api/meetings/{session_id}/speakers/{speakers[0]['id']}",
        json={"displayName": "本地用户"},
    )
    assert rename_response.status_code == 200
    assert rename_response.json()["display_name"] == "本地用户"

    suggestions_response = client.get(f"/api/meetings/{session_id}/suggestions")
    assert suggestions_response.status_code == 200
    assert len(suggestions_response.json()) == 1

    stop_response = client.post(f"/api/meetings/{session_id}/stop")
    assert stop_response.status_code == 200
    assert stop_response.json()["status"] == "stopped"

    export_response = client.get(f"/api/meetings/{session_id}/export?format=markdown")
    assert export_response.status_code == 200
    assert "# 需求评审" in export_response.text
    assert "## 摘要" in export_response.text
    assert "## 待办" in export_response.text
    assert "## 风险" in export_response.text
    assert "## 原始转写" in export_response.text
    assert "本地用户：" in export_response.text


def test_meeting_websocket_accepts_audio_and_pushes_transcript() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/meetings/test-session") as websocket:
        status = websocket.receive_json()

        for seq in range(12):
            websocket.send_json(_audio_frame(seq=seq, rms=0.05))
            level = websocket.receive_json()

        for seq in range(12, 22):
            websocket.send_json(_audio_frame(seq=seq, rms=0.0))
            message = websocket.receive_json()
            if message["type"] == "transcript.final":
                transcript = message
                break
        else:
            raise AssertionError("expected transcript.final after speech and silence frames")

    assert status["type"] == "meeting.status"
    assert status["session_id"] == "test-session"
    assert status["payload"]["status"] == "recording"
    assert level["type"] == "audio.level"
    assert level["payload"]["track"] == "mic"
    assert level["payload"]["isSpeech"] is True
    assert transcript["type"] == "transcript.final"
    assert transcript["payload"]["sessionId"] == "test-session"
    assert transcript["payload"]["isFinal"] is True


def test_system_track_uses_remote_speaker(monkeypatch) -> None:
    db_path = Path("services/ai-service/data") / f"test-{uuid4()}.sqlite3"
    monkeypatch.setenv("MEETING_COPILOT_DB_PATH", str(db_path))
    client = TestClient(app)
    session_id = "system-track-session"

    with client.websocket_connect(f"/ws/meetings/{session_id}") as websocket:
        websocket.receive_json()
        for seq in range(12):
            websocket.send_json(_audio_frame(seq=seq, rms=0.05, session_id=session_id, track="system"))
            websocket.receive_json()
        for seq in range(12, 22):
            websocket.send_json(_audio_frame(seq=seq, rms=0.0, session_id=session_id, track="system"))
            message = websocket.receive_json()
            if message["type"] == "transcript.final":
                transcript = message
                break
        else:
            raise AssertionError("expected system transcript.final")

    assert transcript["payload"]["speaker"] == "Remote"
    transcripts = client.get(f"/api/meetings/{session_id}/transcripts").json()
    assert transcripts[0]["track"] == "system"
    assert transcripts[0]["display_speaker_label"] == "Remote"


def test_settings_and_delete_all_meetings(monkeypatch) -> None:
    db_path = Path("services/ai-service/data") / f"test-{uuid4()}.sqlite3"
    monkeypatch.setenv("MEETING_COPILOT_DB_PATH", str(db_path))
    monkeypatch.setenv("MEETING_COPILOT_LLM_API_KEY", "test-secret")
    client = TestClient(app)

    settings_response = client.get("/api/settings")
    assert settings_response.status_code == 200
    settings = settings_response.json()
    assert settings["apiKeyConfigured"] is True
    assert "test-secret" not in settings_response.text

    update_response = client.put(
        "/api/settings",
        json={
            **settings,
            "llmProvider": "openai-compatible",
            "llmBaseUrl": "https://example.invalid/v1",
            "llmModel": "test-model",
            "cloudLlmEnabled": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["llmProvider"] == "openai-compatible"

    assert client.post("/api/meetings").status_code == 200
    assert len(client.get("/api/meetings").json()) == 1

    delete_response = client.delete("/api/meetings")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] == 1
    assert client.get("/api/meetings").json() == []


def _audio_frame(
    seq: int,
    rms: float,
    session_id: str = "test-session",
    track: str = "mic",
) -> dict:
    return {
        "type": "audio.frame",
        "session_id": session_id,
        "timestamp": "2026-07-03T03:30:00Z",
        "payload": {
            "sessionId": session_id,
            "track": track,
            "timestampMs": 1000 + seq * 20,
            "sampleRate": 16000,
            "channels": 1,
            "format": "pcm_s16le",
            "seq": seq,
            "rms": rms,
            "data": "",
        },
    }
