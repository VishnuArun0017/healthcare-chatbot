from pathlib import Path
import base64
import sys

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from api.main import app  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    from api import main as main_module

    def fake_transcribe(audio_bytes: bytes, language_hint=None):
        return "stub transcript"

    def fake_process_chat_request(request):
        from api.models import ChatResponse, Safety, MentalHealthSafety, PregnancySafety

        safety = Safety(
            red_flag=False,
            matched=[],
            mental_health=MentalHealthSafety(),
            pregnancy=PregnancySafety(),
        )
        response = ChatResponse(
            answer="stub answer",
            route="vector",
            facts=[],
            citations=[],
            safety=safety,
        )
        return response, request.lang, {"total": 0.25, "retrieval": 0.05, "answer_generation": 0.1}

    def fake_synthesize(text: str, language_code: str):
        return b"audio-bytes", "stub-provider", "audio/mpeg"

    monkeypatch.setattr(main_module, "transcribe_audio_bytes", fake_transcribe)
    monkeypatch.setattr(main_module, "process_chat_request", fake_process_chat_request)
    monkeypatch.setattr(main_module, "synthesize_speech", fake_synthesize)

    return TestClient(app)


def test_voice_chat_success(client):
    audio_payload = base64.b64decode("U3R1YiBBdWRpbw==")  # "Stub Audio"
    files = {"audio": ("voice.webm", audio_payload, "audio/webm")}
    response = client.post("/voice-chat", files=files, data={"lang": "hi"})

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "stub transcript"
    assert data["answer"] == "stub answer"
    assert data["audio_base64"] == base64.b64encode(b"audio-bytes").decode("ascii")
    assert data["metadata"]["tts_provider"] == "stub-provider"
    assert data["metadata"]["audio_mime"] == "audio/mpeg"


def test_voice_chat_rejects_non_audio(client):
    files = {"audio": ("voice.txt", b"not audio", "text/plain")}
    response = client.post("/voice-chat", files=files)
    assert response.status_code == 400
    assert "Unsupported media type" in response.json()["detail"]

