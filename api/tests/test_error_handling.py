import io
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from api.main import app, rate_limiter  # noqa: E402


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    original_limit = rate_limiter.limit
    original_window = rate_limiter.window
    rate_limiter.configure(limit=10, window=60)
    rate_limiter.requests.clear()
    yield
    rate_limiter.configure(limit=original_limit, window=original_window)
    rate_limiter.requests.clear()


@pytest.fixture
def client(monkeypatch):
    from api import main as main_module

    def fake_translate(text: str, target_lang: str, src_lang: str | None = None) -> str:
        return text

    class DummyCompletion:
        def __init__(self, content: str = "stub completion") -> None:
            self.choices = [
                SimpleNamespace(message=SimpleNamespace(content=content))
            ]

    class DummyCompletions:
        def create(self, *args: Any, **kwargs: Any) -> DummyCompletion:
            return DummyCompletion()

    class DummyChat:
        completions = DummyCompletions()

    class DummyTranscriptions:
        @staticmethod
        def create(*args: Any, **kwargs: Any):
            return SimpleNamespace(text="dummy transcription")

    class DummyAudio:
        transcriptions = DummyTranscriptions()

    class DummyOpenAI:
        chat = DummyChat()
        audio = DummyAudio()

    monkeypatch.setattr(main_module, "translate_text", fake_translate)
    monkeypatch.setattr(main_module, "retrieve", lambda query, k=4: [])
    monkeypatch.setattr(main_module, "get_openai_client", lambda: DummyOpenAI())

    return TestClient(app)


def test_chat_empty_text_returns_422(client):
    response = client.post(
        "/chat",
        json={
            "text": "   ",
            "lang": "en",
            "profile": {"diabetes": False, "hypertension": False, "pregnancy": False},
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("Query text must not be empty" in str(err) for err in detail)


def test_rate_limit_returns_429(client):
    rate_limiter.configure(limit=1, window=60)
    rate_limiter.requests.clear()

    payload = {
        "text": "I feel dizzy",
        "lang": "en",
        "profile": {"diabetes": False, "hypertension": False, "pregnancy": False},
    }

    first = client.post("/chat", json=payload)
    assert first.status_code == 200

    second = client.post("/chat", json=payload)
    assert second.status_code == 429
    assert second.json()["detail"] == "Too many requests. Please try again later."


def test_stt_rejects_invalid_file_type(client):
    audio_bytes = io.BytesIO(b"not really audio")
    files = {"file": ("test.txt", audio_bytes, "text/plain")}
    response = client.post("/stt", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported media type. Please upload an audio file."


def test_chat_fallback_when_openai_unavailable(client, monkeypatch):
    from api import main as main_module

    monkeypatch.setattr(main_module, "get_openai_client", lambda: None)
    monkeypatch.setattr(
        main_module,
        "retrieve",
        lambda query, k=4: [
            {
                "chunk": "General fever guidance.",
                "id": "guidance#0",
                "source": "test.md",
                "topic": "fever",
                "category": "general",
            }
        ],
    )

    payload = {
        "text": "Tell me about fever",
        "lang": "en",
        "profile": {"diabetes": False, "hypertension": False, "pregnancy": False},
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    assert "I cannot provide medical diagnosis" in response.json()["answer"]


def test_chat_handles_internal_error(client, monkeypatch):
    from api import main as main_module

    def boom(_: Any) -> Any:
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(main_module, "process_chat_request", boom)

    payload = {
        "text": "Help me breathe better",
        "lang": "en",
        "profile": {"diabetes": False, "hypertension": False, "pregnancy": False},
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 500
    assert "Unable to process your request" in response.json()["detail"]


def test_profile_age_validation(client):
    payload = {
        "text": "I have fever",
        "lang": "en",
        "profile": {"age": -5, "diabetes": False, "hypertension": False, "pregnancy": False},
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 422
    details = response.json()["detail"]
    assert any("Age cannot be negative" in (err.get("msg") or "") for err in details)


def test_stt_empty_audio_returns_400(client):
    audio_bytes = io.BytesIO(b"")
    files = {"file": ("empty.webm", audio_bytes, "audio/webm")}
    response = client.post("/stt", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty audio file received."


def test_stt_without_openai_returns_503(client, monkeypatch):
    from api import main as main_module

    monkeypatch.setattr(main_module, "get_openai_client", lambda: None)
    audio_bytes = io.BytesIO(b"\x00\x01")
    files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
    response = client.post("/stt", files=files)
    assert response.status_code == 503
    assert response.json()["detail"] == "Speech service unavailable"


def test_chat_openai_unavailable_returns_fallback(client, monkeypatch):
    from api import main as main_module

    monkeypatch.setattr(main_module, "get_openai_client", lambda: None)
    monkeypatch.setattr(
        main_module,
        "retrieve",
        lambda query, k=4: [
            {
                "chunk": "General lifestyle guidance.",
                "id": "guidance#1",
                "source": "test.md",
                "topic": "general",
                "category": "general",
            }
        ],
    )
    response = client.post(
        "/chat",
        json={
            "text": "I need general advice",
            "lang": "en",
            "profile": {"diabetes": False, "hypertension": False, "pregnancy": False},
        },
    )
    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "I'm here to help with health questions" in answer
    assert "general information only" in answer


def test_chat_invalid_age_validation(client):
    response = client.post(
        "/chat",
        json={
            "text": "Help me",
            "lang": "en",
            "profile": {
                "diabetes": False,
                "hypertension": False,
                "pregnancy": False,
                "age": -5,
            },
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("Age cannot be negative" in str(err.get("ctx", {}).get("error", "")) for err in detail)


def test_health_endpoint_reports_services(client, monkeypatch):
    from api import main as main_module

    monkeypatch.setattr(main_module, "ensure_neo4j", lambda: False)
    response = client.get("/health")
    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert "services" in body
    assert body["services"]["graph"] is False


def test_graph_get_providers_falls_back(monkeypatch):
    from api import main as main_module

    city = "Mumbai"

    monkeypatch.setattr(main_module, "ensure_neo4j", lambda: True)

    def raise_error(city_name):
        raise RuntimeError("neo failure")

    monkeypatch.setattr(main_module, "neo4j_get_providers_in_city", raise_error)

    fallback_called = {}

    def fake_fallback(city_name):
        fallback_called["city"] = city_name
        return [{"provider": "Fallback Clinic", "mode": "visit"}]

    monkeypatch.setattr(main_module.graph_fallback, "get_providers_in_city", fake_fallback)

    result = main_module.graph_get_providers(city)
    assert result == [{"provider": "Fallback Clinic", "mode": "visit"}]
    assert fallback_called["city"] == city

