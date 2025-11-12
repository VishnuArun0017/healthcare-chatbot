"""Simple CLI to evaluate IndicTrans2 romanized translation accuracy."""

from __future__ import annotations

import json
import os
import sys
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Tuple

from dotenv import load_dotenv

here = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(here)
if os.path.exists(os.path.join(project_root, ".env")):
    load_dotenv(os.path.join(project_root, ".env"))
if os.path.exists(os.path.join(here, ".env")):
    load_dotenv(os.path.join(here, ".env"))

# Support legacy env var name found in some setups.
if os.getenv("TRANS_HF_TOKEN") and not (
    os.getenv("INDIC_TRANS_HF_TOKEN") or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
):
    os.environ.setdefault("INDIC_TRANS_HF_TOKEN", os.getenv("TRANS_HF_TOKEN"))

from services.indic_translator import IndicTransService  # noqa: E402  (after dotenv)


@dataclass
class TestCase:
    lang: str
    romanized: str
    expected_en: str


TEST_CASES: List[TestCase] = [
    # Tamil
    TestCase("ta", "naa toongitan", "I slept"),
    TestCase("ta", "enakku pasikuduthu", "I am hungry"),
    TestCase("ta", "nee epdi iruka?", "How are you?"),
    TestCase("ta", "naan velaila poren", "I am going to work"),
    TestCase("ta", "indha paatu romba nalla iruku", "This song is really good"),
    # Malayalam
    TestCase("ml", "njan kazhichu", "I ate"),
    TestCase("ml", "ninakku sukhamano?", "Are you fine?"),
    TestCase("ml", "ente peru anu rahul", "My name is Rahul"),
    TestCase("ml", "njan veettil aanu", "I am at home"),
    TestCase("ml", "ithu nalla pusthakam aanu", "This is a good book"),
    # Hindi
    TestCase("hi", "main thak gaya hoon", "I am tired"),
    TestCase("hi", "tum kahan ja rahe ho?", "Where are you going?"),
    TestCase("hi", "mujhe bhook lagi hai", "I am hungry"),
    TestCase("hi", "aaj mausam bahut accha hai", "The weather is very nice today"),
    TestCase("hi", "mujhe yeh pasand hai", "I like this"),
    # Kannada
    TestCase("kn", "nanu oota maadide", "I have eaten"),
    TestCase("kn", "neenu hegiddiya?", "How are you?"),
    TestCase("kn", "nan hesaru praveen", "My name is Praveen"),
    TestCase("kn", "nanu kelasa ge hogtha idini", "I am going to work"),
    TestCase("kn", "ee haadu tumba chennagide", "This song is very nice"),
    # Telugu
    TestCase("te", "nenu tinanu", "I ate"),
    TestCase("te", "nee peru emiti?", "What is your name?"),
    TestCase("te", "nenu baagunnanu", "I am fine"),
    TestCase("te", "idi chala manchidi", "This is very good"),
    TestCase("te", "nenu intiki veltunna", "I am going home"),
]


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip().lower()


def evaluate(service: IndicTransService, cases: List[TestCase]) -> Dict[str, Dict[str, int]]:
    stats: Dict[str, Dict[str, int]] = {}
    print("=== IndicTrans2 Romanized -> English Accuracy ===")
    print()
    if not service.is_enabled():
        print("⚠️ IndicTransService is disabled (missing dependencies or token).")
        print("   Ensure torch/transformers/IndicTransToolkit are installed and HF token is set.")
        sys.exit(1)

    for case in cases:
        lang_bucket = stats.setdefault(case.lang, {"passed": 0, "failed": 0, "total": 0})
        result = service.translate_romanized_to_english(case.romanized, case.lang)
        lang_bucket["total"] += 1
        translated = result.translated_text or ""
        normalized_match = normalize(translated) == normalize(case.expected_en)
        if normalized_match:
            lang_bucket["passed"] += 1
        else:
            lang_bucket["failed"] += 1

        print(
            json.dumps(
                {
                    "language": case.lang,
                    "input": case.romanized,
                    "expected": case.expected_en,
                    "output": translated,
                    "provider": result.provider,
                    "details": result.details,
                    "success": normalized_match,
                },
                ensure_ascii=False,
            )
        )

    print()
    print("=== Summary ===")
    grand_total = 0
    grand_pass = 0
    for lang, bucket in stats.items():
        total = bucket["total"]
        passed = bucket["passed"]
        failed = bucket["failed"]
        grand_total += total
        grand_pass += passed
        pct = (passed / total * 100) if total else 0.0
        print(f"{lang}: {passed}/{total} ({pct:.1f}% pass)  | failed={failed}")

    if grand_total:
        overall_pct = grand_pass / grand_total * 100
        print(f"\nOverall: {grand_pass}/{grand_total} ({overall_pct:.1f}% pass)")

    return stats


def main() -> None:
    service = IndicTransService()
    evaluate(service, TEST_CASES)


if __name__ == "__main__":
    main()


