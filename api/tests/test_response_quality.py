from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from api.main import app, FALLBACK_MESSAGE_EN, DISCLAIMER_EN  # noqa: E402


client = TestClient(app)


@pytest.fixture(autouse=True)
def stub_external_dependencies(monkeypatch):
    def fake_translate(text: str, target_lang: str, src_lang: str | None = None) -> str:
        return f"{text}[{target_lang}]"

    def fake_detect_language(_: str) -> str:
        return "en"

    def fake_retrieve(_: str, k: int = 4):
        return [
            {
                "chunk": "Sample clinical guidance chunk.",
                "id": "sample#0",
                "source": "sample/source.md",
                "title": "Sample Title",
                "category": "general",
            }
            for _ in range(k)
        ]

    monkeypatch.setattr("api.main.translate_text", fake_translate)
    monkeypatch.setattr("api.main.detect_language", fake_detect_language)
    monkeypatch.setattr("api.main.retrieve", fake_retrieve)
    monkeypatch.setattr("api.main.is_graph_intent", lambda _: False)
    monkeypatch.setattr("api.main.get_openai_client", lambda: None)


@pytest.mark.parametrize("lang_code", ["hi", "ta", "te", "kn", "ml"])
def test_multilingual_response_localizes_output(lang_code: str):
    payload = {
        "text": "I want to kill myself and my baby is not moving.",
        "lang": lang_code,
        "profile": {
            "age": 28,
            "sex": "female",
            "diabetes": False,
            "hypertension": False,
            "pregnancy": True,
            "city": "Delhi",
        },
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["route"] == "vector"
    assert data["citations"]  # ensure citations preserved

    answer = data["answer"]
    assert f"{FALLBACK_MESSAGE_EN}[{lang_code}]" in answer
    assert f"{DISCLAIMER_EN}[{lang_code}]" in answer

    facts = data["facts"]
    mental_fact = next(f for f in facts if f["type"] == "mental_health_crisis")
    assert all(action.endswith(f"[{lang_code}]") for action in mental_fact["data"]["actions"])

    pregnancy_fact = next(f for f in facts if f["type"] == "pregnancy_alert")
    assert all(
        guidance.endswith(f"[{lang_code}]")
        for guidance in pregnancy_fact["data"]["guidance"]
    )

    safety = data["safety"]
    assert all(
        first_aid_instruction.endswith(f"[{lang_code}]")
        for first_aid_instruction in safety["mental_health"]["first_aid"]
    )

