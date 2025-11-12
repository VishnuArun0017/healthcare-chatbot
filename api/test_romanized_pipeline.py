import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv


def ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def load_environment() -> None:
    api_dir = Path(__file__).resolve().parent
    candidates = [api_dir / ".env", api_dir.parent / ".env"]
    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate)
            return
    load_dotenv()


def pretty_print(label: str, payload: Dict[str, Any]) -> None:
    print(f"\n[{label}]")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def print_pipeline_trace(metadata: Dict[str, Any]) -> None:
    debug = metadata.get("debug") if metadata else None
    print("\n--- Pipeline Trace ---")
    if not debug:
        print("No debug information available. Ensure the chat payload includes 'debug': true.")
        return

    print(f"Input (romanized): {debug.get('input_text')}")
    print(f"Detected language: {debug.get('detected_language')}  |  Requested: {debug.get('requested_language')}")
    romanized = debug.get("romanized_detected_language")
    if romanized:
        print(f"Romanized guess: {romanized}")

    print("\nStep 1) Normalize → English")
    print(f"  Source language used: {debug.get('processed_text_source_language')}")
    if debug.get("native_script_variant"):
        print(f"  Native-script intermediate: {debug.get('native_script_variant')}")
    print(f"  English translation: {debug.get('processed_text_en')}")

    print("\nStep 2) RAG / Neo4j context")
    rag_snippets = debug.get("rag_context_snippets") or []
    print(f"  Context chunks retrieved: {len(rag_snippets)}")
    for idx, snippet in enumerate(rag_snippets[:2], start=1):
        preview = snippet.replace("\n", " ")[:160]
        print(f"    [{idx}] {preview}")

    citations = debug.get("citations") or []
    if citations:
        print("  Sources:")
        for cite in citations:
            topic = cite.get("topic") or cite.get("source")
            print(f"    - {topic} ({cite.get('id')})")
    else:
        print("  Sources: none")

    print("\nStep 3) Model response (English)")
    llm = debug.get("llm") or {}
    provider = llm.get("provider") or "fallback"
    model = llm.get("model") or "-"
    print(f"  Provider: {provider}  |  Model: {model}")
    if llm.get("fallback"):
        print(f"  Fallback reason: {llm.get('reason')}")
    print(f"  Model output: {debug.get('answer_en')}")

    print("\nStep 4) Localized output")
    print(f"  Output style: {metadata.get('response_style')}  |  Target language: {metadata.get('target_language')}")
    print(f"  Final response: {debug.get('answer_localized')}")

    print("\nStep 5) Timings")
    timings = metadata.get("timings") or {}
    for key, value in timings.items():
        print(f"  {key}: {value:.3f}s")
    print("--- End Trace ---\n")


def check_health(client: httpx.Client, base_url: str) -> None:
    response = client.get(f"{base_url}/health", timeout=15)
    response.raise_for_status()
    data = response.json()
    pretty_print("health", data)
    if not (data.get("openai_configured") or data.get("openrouter_configured")):
        raise SystemExit("Neither OpenAI nor OpenRouter is configured. Please set API keys before running tests.")


def run_chat_case(
    client: httpx.Client,
    base_url: str,
    text: str,
    lang: Optional[str],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"text": text, "profile": profile, "debug": True}
    if lang:
        payload["lang"] = lang

    response = client.post(f"{base_url}/chat", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    print_pipeline_trace(data.get("metadata") or {})
    return data


def main() -> int:
    ensure_utf8_stdout()
    load_environment()

    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    profile = {
        "age": 32,
        "sex": "female",
        "diabetes": False,
        "hypertension": False,
        "pregnancy": False,
    }

    test_cases: List[Dict[str, Any]] = [
        {
            "description": "Romanized Tamil – headache complaint",
            "text": "dai ennachu thala valikuthu da",
            "lang": "en",
        },
        {
            "description": "Romanized Hindi – stomach pain",
            "text": "bhai pet me bahut dard ho raha hai",
            "lang": "en",
        },
        {
            "description": "Romanized Telugu – fever and weakness",
            "text": "nenu uppirintha bala ledu fever vundi",
            "lang": "en",
        },
    ]

    with httpx.Client(timeout=120) as client:
        check_health(client, base_url)

        for case in test_cases:
            print(f"\n=== {case['description']} ===")
            try:
                run_chat_case(
                    client,
                    base_url,
                    case["text"],
                    case.get("lang"),
                    profile,
                )
            except httpx.HTTPStatusError as exc:
                print(f"Request failed with status {exc.response.status_code}: {exc.response.text}")
            except Exception as exc:  # pragma: no cover - diagnostic
                print(f"Unexpected error: {exc}")

    print("\n✅ Romanized text pipeline smoke test complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

