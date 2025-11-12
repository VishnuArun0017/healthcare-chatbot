import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Quick smoke test for STT + chat pipeline against a running backend."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL where the FastAPI server is running.",
    )
    parser.add_argument(
        "--audio",
        type=Path,
        help="Audio file to send to /stt (webm/wav/m4a). If omitted, --text is required.",
    )
    parser.add_argument(
        "--text",
        help="Fallback text to send to /chat when no audio is provided.",
    )
    parser.add_argument(
        "--lang",
        default=None,
        help="Optional language hint (en, hi, ta, te, kn, ml) for STT and chat.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=90.0,
        help="HTTP timeout in seconds for each request.",
    )
    return parser


def load_environment() -> None:
    root = Path(__file__).resolve().parent
    env_candidates = [
        root / ".env",
        root.parent / ".env",
    ]
    for candidate in env_candidates:
        if candidate.exists():
            load_dotenv(candidate)
            return
    load_dotenv()


def ensure_service_available(client: httpx.Client, base_url: str) -> None:
    resp = client.get(f"{base_url}/health")
    resp.raise_for_status()
    data = resp.json()
    print("\n[health]", json.dumps(data, indent=2))
    if not data.get("openai_configured"):
        raise SystemExit(
            "OpenAI client is not configured according to /health. "
            "Set OPENAI_API_KEY (or restart the server) and retry."
        )


def run_stt(
    client: httpx.Client, base_url: str, audio_path: Path, lang: str | None
) -> str:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    content_type, _ = mimetypes.guess_type(str(audio_path))
    if content_type is None:
        content_type = "application/octet-stream"

    with audio_path.open("rb") as audio_file:
        files = {"file": (audio_path.name, audio_file, content_type)}
        params = {"lang": lang} if lang else None
        resp = client.post(f"{base_url}/stt", files=files, params=params)
    resp.raise_for_status()
    data = resp.json()
    transcript = data.get("text", "")
    print("\n[stt]", json.dumps(data, ensure_ascii=False, indent=2))
    if not transcript:
        raise SystemExit("Speech-to-text succeeded but returned empty transcript.")
    return transcript


def run_chat(client: httpx.Client, base_url: str, text: str, lang: str | None) -> dict:
    payload = {
        "text": text,
        "lang": lang or "en",
        "profile": {
            "age": 30,
            "sex": "female",
            "diabetes": False,
            "hypertension": False,
            "pregnancy": False,
            "city": "Chennai",
        },
    }
    resp = client.post(f"{base_url}/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    print("\n[chat]", json.dumps(data, ensure_ascii=False, indent=2))
    return data


def main(argv: list[str]) -> int:
    load_environment()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.audio and not args.text:
        parser.error("Provide --audio for STT or --text for direct chat (or both).")

    base_url = args.base_url.rstrip("/")

    headers = {"Accept": "application/json"}
    with httpx.Client(timeout=args.timeout, headers=headers) as client:
        ensure_service_available(client, base_url)

        transcript = args.text
        if args.audio:
            transcript = run_stt(client, base_url, args.audio, args.lang)
            print(f"\n[stt] Transcript: {transcript}")

        if not transcript:
            raise SystemExit("No input text available for /chat request.")

        run_chat(client, base_url, transcript, args.lang)

    print("\n✅ Pipeline check complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

