import json
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv


def load_environment() -> None:
    """Load .env from api/ or project root."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, ".env"),
        os.path.join(os.path.dirname(here), ".env"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            load_dotenv(candidate)
            return
    load_dotenv()


def build_headers() -> Dict[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")

    referer = os.getenv("OPENROUTER_SITE_URL", "http://localhost")
    title = os.getenv("OPENROUTER_SITE_NAME", "Healthcare Chatbot")

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": referer,
        "X-Title": title,
    }


def main() -> int:
    load_environment()

    model = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-r1-0528:free")
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "bro ennachu thala valikkuthu edachu home remedy irruka?",
            }
        ],
        "temperature": 0.2,
        "max_tokens": 150,
    }

    print(f"Using model: {model}")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=build_headers(),
        data=json.dumps(payload),
        timeout=60,
    )

    print(f"Status: {response.status_code}")
    try:
        body = response.json()
    except ValueError:
        body = {"error": "Non-JSON response", "content": response.text}

    print("Response JSON:")
    print(json.dumps(body, indent=2, ensure_ascii=False))

    if response.status_code != 200:
        return 1

    choice = body.get("choices", [{}])[0]
    message = choice.get("message", {})
    content = message.get("content")
    print("\nAssistant reply:")
    print(content or "<empty>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


