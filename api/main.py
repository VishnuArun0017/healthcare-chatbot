import asyncio
import base64
import copy
import json
import logging
import os
import tempfile
import time
from collections import defaultdict, deque
from io import BytesIO
from typing import Any, Deque, Dict, List, Optional, Tuple

from deep_translator import GoogleTranslator  # type: ignore
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langdetect import LangDetectException, detect  # type: ignore
from openai import OpenAI
from starlette.middleware.base import RequestResponseEndpoint

try:
    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs
except Exception:  # pragma: no cover
    ElevenLabs = None
    VoiceSettings = None

try:
    from gtts import gTTS
except Exception:  # pragma: no cover
    gTTS = None

os.environ.setdefault("CHROMADB_DISABLE_TELEMETRY", "1")

from .safety import (
    detect_red_flags,
    detect_mental_health_crisis,
    detect_pregnancy_emergency,
    extract_symptoms,
)
from .router import is_graph_intent, extract_city
from .rag.retriever import retrieve
from .models import ChatRequest, ChatResponse, Profile, VoiceChatResponse

from .graph import fallback as graph_fallback
from .graph.cypher import (
    get_red_flags as neo4j_get_red_flags,
    get_contraindications as neo4j_get_contraindications,
    get_providers_in_city as neo4j_get_providers_in_city,
    get_safe_actions_for_metabolic_conditions as neo4j_get_safe_actions,
)
from .graph.client import neo4j_client

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("health_assistant")

app = FastAPI(title="Health Assistant API")


@app.on_event("shutdown")
async def _shutdown() -> None:
    if neo4j_client.driver:
        neo4j_client.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimpleRateLimiter:
    def __init__(self, limit: int = 30, window: int = 60) -> None:
        self.limit = limit
        self.window = window
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)

    def configure(self, *, limit: Optional[int] = None, window: Optional[int] = None) -> None:
        if limit is not None:
            self.limit = limit
        if window is not None:
            self.window = window

    async def __call__(self, request: Request, call_next: RequestResponseEndpoint):
        if os.getenv("DISABLE_RATE_LIMIT") == "1" or self.limit <= 0:
            return await call_next(request)

        identifier = request.client.host if request.client else "anonymous"
        now = time.time()
        bucket = self.requests[identifier]

        while bucket and now - bucket[0] > self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:
            logger.warning("Rate limit exceeded", extra={"client": identifier})
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )

        bucket.append(now)
        response = await call_next(request)
        return response


rate_limiter = SimpleRateLimiter(
    limit=int(os.getenv("RATE_LIMIT", "30")),
    window=int(os.getenv("RATE_WINDOW", "60")),
)

if os.getenv("DISABLE_RATE_LIMIT") != "1":
    app.middleware("http")(rate_limiter)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    for error in errors:
        ctx = error.get("ctx")
        if ctx and "error" in ctx:
            ctx["error"] = str(ctx["error"])

    logger.warning(
        "Validation error",
        extra={"path": request.url.path, "errors": errors, "body": exc.body},
    )
    payload = jsonable_encoder({"detail": errors})
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP error",
        extra={"path": request.url.path, "status_code": exc.status_code, "detail": exc.detail},
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

LANGUAGE_LABELS: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
}

SUPPORTED_LANG_CODES = set(LANGUAGE_LABELS.keys())
DEFAULT_LANG = "en"

FALLBACK_MESSAGE_EN = (
    "I'm here to help with health questions. Please note: I cannot provide medical diagnosis. "
    "For emergencies, call 108 or visit the nearest hospital."
)

DISCLAIMER_EN = (
    "⚠️ This is general information only, not medical advice. Consult a healthcare professional for proper diagnosis and treatment."
)

PREGNANCY_ALERT_GUIDANCE_EN = [
    "Severe pregnancy symptoms need urgent medical review.",
    "Contact your obstetrician or emergency services immediately.",
]

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_VOICE_DEFAULT = os.getenv("ELEVENLABS_VOICE", "Bella")
ELEVENLABS_VOICE_MAP = {
    "en": os.getenv("ELEVENLABS_VOICE_EN", ELEVENLABS_VOICE_DEFAULT),
    "hi": os.getenv("ELEVENLABS_VOICE_HI", ELEVENLABS_VOICE_DEFAULT),
    "ta": os.getenv("ELEVENLABS_VOICE_TA", ELEVENLABS_VOICE_DEFAULT),
    "te": os.getenv("ELEVENLABS_VOICE_TE", ELEVENLABS_VOICE_DEFAULT),
    "kn": os.getenv("ELEVENLABS_VOICE_KN", ELEVENLABS_VOICE_DEFAULT),
    "ml": os.getenv("ELEVENLABS_VOICE_ML", ELEVENLABS_VOICE_DEFAULT),
}

GTTS_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
}

_eleven_client: Optional["ElevenLabs"] = None

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "en"


def translate_text(text: str, target_lang: str, src_lang: Optional[str] = None) -> str:
    if not text.strip():
        return text

    if src_lang and src_lang == target_lang:
        return text

    try:
        translator = GoogleTranslator(
            source=src_lang if src_lang else "auto",
            target=target_lang,
        )
        return translator.translate(text)
    except Exception as exc:
        logger.warning(
            "Translation error",
            extra={"source": src_lang or "auto", "target": target_lang, "error": str(exc)},
        )
        return text


def localize_text(text: str, target_lang: str, src_lang: str = "en") -> str:
    if target_lang == src_lang:
        return text
    return translate_text(text, target_lang=target_lang, src_lang=src_lang)


def get_language_label(code: str) -> str:
    return LANGUAGE_LABELS.get(code, LANGUAGE_LABELS[DEFAULT_LANG])


def get_localized_disclaimer(lang: str) -> str:
    return localize_text(DISCLAIMER_EN, target_lang=lang)


def localize_list(entries: List[str], lang: str, src_lang: str = "en") -> List[str]:
    if lang == src_lang:
        return entries
    return [translate_text(item, target_lang=lang, src_lang=src_lang) for item in entries]


def get_elevenlabs_client() -> Optional["ElevenLabs"]:
    global _eleven_client
    if _eleven_client is None and ELEVENLABS_API_KEY and ElevenLabs:
        try:
            _eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to initialise ElevenLabs client", extra={"error": str(exc)})
            _eleven_client = None
    return _eleven_client


def transcribe_audio_bytes(audio_bytes: bytes, *, language_hint: Optional[str] = None) -> str:
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=503, detail="Speech service unavailable")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio data received.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            payload: Dict[str, Any] = {
                "model": "whisper-1",
                "file": audio_file,
            }
            if language_hint and language_hint in SUPPORTED_LANG_CODES:
                payload["language"] = language_hint
            transcription = client.audio.transcriptions.create(**payload)
        logger.info(
            "Speech-to-text processed successfully",
            extra={"bytes": len(audio_bytes), "language_hint": language_hint},
        )
        return transcription.text
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Whisper transcription failed")
        raise HTTPException(status_code=502, detail=f"STT error: {str(exc)}") from exc
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:  # pragma: no cover
            pass


def synthesize_speech(text: str, language_code: str) -> Tuple[bytes, str, str]:
    text = text.strip()
    if not text:
        return b"", "none", "text/plain"

    # Try ElevenLabs first if configured
    if ELEVENLABS_API_KEY and ElevenLabs:
        client = get_elevenlabs_client()
        voice = ELEVENLABS_VOICE_MAP.get(language_code, ELEVENLABS_VOICE_DEFAULT)
        if client:
            try:
                audio_iter = client.generate(
                    text=text,
                    voice=voice,
                    model=ELEVENLABS_MODEL,
                    voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.75)
                    if VoiceSettings
                    else None,
                )
                audio_bytes = b"".join(audio_iter)
                return audio_bytes, "elevenlabs", "audio/mpeg"
            except Exception as exc:  # pragma: no cover
                logger.warning("ElevenLabs synthesis failed", extra={"error": str(exc)})

    if gTTS:
        lang = GTTS_LANG_MAP.get(language_code, "en")
        try:
            tts = gTTS(text=text, lang=lang)
            buffer = BytesIO()
            tts.write_to_fp(buffer)
            return buffer.getvalue(), "gtts", "audio/mpeg"
        except Exception as exc:  # pragma: no cover
            logger.warning("gTTS synthesis failed", extra={"error": str(exc), "lang": lang})

    logger.warning("Falling back to text-only response for TTS", extra={"lang": language_code})
    return b"", "text-only", "text/plain"


def encode_audio_base64(audio_bytes: bytes) -> str:
    if not audio_bytes:
        return ""
    return base64.b64encode(audio_bytes).decode("ascii")


openai_api_key = os.getenv("OPENAI_API_KEY")
_openai_client: Optional[OpenAI] = None
_neo4j_available: Optional[bool] = None


def get_openai_client() -> Optional[OpenAI]:
    global _openai_client
    if _openai_client is None and openai_api_key:
        try:
            _openai_client = OpenAI(api_key=openai_api_key)
        except Exception as exc:
            logger.error("OpenAI client initialization error", extra={"error": str(exc)})
            _openai_client = None
    return _openai_client


def ensure_neo4j() -> bool:
    global _neo4j_available
    if _neo4j_available is None:
        try:
            _neo4j_available = neo4j_client.connect()
            if not _neo4j_available:
                logger.warning("Neo4j connection unavailable, falling back to in-memory graph")
        except Exception as exc:
            logger.error("Neo4j connection error", extra={"error": str(exc)})
            _neo4j_available = False
    return bool(_neo4j_available)


def build_personalization_notes(profile: Profile) -> List[str]:
    notes: List[str] = []

    if profile.age is not None:
        if profile.age < 2:
            notes.append(
                "User is an infant (<2 years). Avoid medication dosing advice and urge immediate pediatric review if symptoms worsen."
            )
        elif profile.age < 12:
            notes.append(
                "User is a child (<12 years). Provide caregiver-friendly guidance and highlight when to see a pediatrician."
            )
        elif profile.age >= 65:
            notes.append(
                "User is an older adult (65+). Emphasise monitoring chronic conditions and the risks of medication interactions."
            )

    if profile.pregnancy:
        notes.append(
            "User is currently pregnant. Avoid contraindicated medicines and recommend contacting the obstetric team for concerning symptoms."
        )

    return notes


def graph_get_red_flags(symptoms: List[str]) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_red_flags(symptoms)
        except Exception as exc:
            logger.error("Neo4j red flag query failed", extra={"error": str(exc)})
    return graph_fallback.get_red_flags(symptoms)


def graph_get_contraindications(user_conditions: List[str]) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_contraindications(user_conditions)
        except Exception as exc:
            logger.error("Neo4j contraindications query failed", extra={"error": str(exc)})
    return graph_fallback.get_contraindications(user_conditions)


def graph_get_providers(city: str) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_providers_in_city(city)
        except Exception as exc:
            logger.error("Neo4j provider query failed", extra={"error": str(exc), "city": city})
    return graph_fallback.get_providers_in_city(city)


def graph_get_safe_actions(user_conditions: List[str]) -> List[Dict[str, Any]]:
    if not user_conditions:
        return []
    
    if ensure_neo4j():
        try:
            return neo4j_get_safe_actions()
        except Exception as exc:
            logger.error("Neo4j safe actions query failed", extra={"error": str(exc)})
    return graph_fallback.get_safe_actions(user_conditions)


def build_fact_blocks(facts: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Prepare fact summaries for LLM context and for direct display.
    """
    if not facts:
        return "", ""

    llm_lines: List[str] = []
    display_lines: List[str] = []

    for fact in facts:
        f_type = fact.get("type")
        data = fact.get("data", [])

        if f_type == "contraindications":
            for entry in data:
                condition = entry.get("condition")
                avoids = ", ".join(entry.get("avoid", []))
                llm_lines.append(f"- Contraindications for {condition}: avoid {avoids}")
                display_lines.append(f"{condition}: avoid {avoids}")
        elif f_type == "safe_actions":
            for entry in data:
                condition = entry.get("condition")
                actions = ", ".join(entry.get("actions", []))
                llm_lines.append(f"- Safe actions for {condition}: {actions}")
                display_lines.append(f"{condition}: {actions}")
        elif f_type == "mental_health_crisis":
            matched = ", ".join(data.get("matched", []))
            actions = "; ".join(data.get("actions", []))
            llm_lines.append(f"- Mental health crisis detected (phrases: {matched}). First aid: {actions}")
            display_lines.append(f"Mental health crisis phrases ({matched}) → {actions}")
        elif f_type == "pregnancy_alert":
            matched = ", ".join(data.get("matched", []))
            guidance = "; ".join(data.get("guidance", []))
            llm_lines.append(f"- Pregnancy alert indicators ({matched}). Guidance: {guidance}")
            display_lines.append(f"Pregnancy alert ({matched}) → {guidance}")
        elif f_type == "providers":
            providers = "; ".join(
                f"{item.get('provider')} ({item.get('mode', 'care')})"
                for item in data
            )
            llm_lines.append(f"- Local providers: {providers}")
            display_lines.append(f"Providers → {providers}")
        elif f_type == "red_flags":
            for entry in data:
                symptom = entry.get("symptom")
                conditions = ", ".join(entry.get("conditions", []))
                llm_lines.append(f"- Red flag: {symptom} → {conditions}")
                display_lines.append(f"{symptom} → {conditions}")
        elif f_type == "personalization":
            for note in data:
                llm_lines.append(f"- Personalization note: {note}")
                display_lines.append(note)

    llm_summary = "\n".join(llm_lines)
    display_summary = "\n".join(display_lines)
    return llm_summary, display_summary


def localize_fact_guidance(facts: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    if lang == "en":
        return facts

    localized = copy.deepcopy(facts)
    for fact in localized:
        if fact.get("type") == "mental_health_crisis":
            actions = fact.get("data", {}).get("actions", [])
            fact["data"]["actions"] = localize_list(actions, lang)
        elif fact.get("type") == "pregnancy_alert":
            guidance = fact.get("data", {}).get("guidance", [])
            fact["data"]["guidance"] = localize_list(guidance, lang)
    return localized


def generate_answer(
    *,
    context: str,
    query_en: str,
    target_lang: str,
    language_label: str,
    original_query: str,
    facts: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
) -> str:
    """Generate answer using OpenAI or fallback"""
    client = get_openai_client()
    if not client:
        logger.warning("OpenAI client unavailable, returning fallback response")
        return localize_text(FALLBACK_MESSAGE_EN, target_lang=target_lang)

    fact_summary, _ = build_fact_blocks(facts)

    citations_section = ""
    if citations:
        lines = []
        for idx, cite in enumerate(citations, start=1):
            source = cite.get("source", "unknown")
            topic = cite.get("topic")
            cite_id = cite.get("id")
            label = f"{source}" if not topic else f"{topic} ({source})"
            lines.append(f"[{idx}] {label} — {cite_id}")
        citations_section = "\n".join(lines)
    
    system_prompt = """You are a helpful health assistant. Provide clear, accurate health information based on the context provided.

IMPORTANT GUIDELINES:
- You are NOT a doctor and cannot diagnose
- Provide general health information only
- Always include a disclaimer about seeking professional medical care
- Be empathetic and supportive
- Keep answers concise (3-4 short paragraphs) plus a short source list
- Structure answers as:
  1. What the symptoms might indicate (non-diagnostic)
  2. Safe self-care guidance
  3. When to escalate to a healthcare professional
  4. Mandatory disclaimer
- Integrate database facts when helpful (contraindications, safe actions, providers, alerts)
- If facts indicate emergencies or crises, emphasise them clearly
- Respond in the target language exactly as requested: use simple, clear Hindi for Hindi; otherwise English
- End with a 'Sources:' section referencing the provided citations by number."""

    user_prompt = f"""Context from medical knowledge base (in English):
{context}

Structured facts to emphasise:
{fact_summary or 'None provided.'}

User question (original): {original_query}
User question (English): {query_en}

Language for response: {language_label}

Citations to reference:
{citations_section or 'No citations supplied.'}

Produce a helpful, non-diagnostic response following the required structure and include a Sources section."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("OpenAI completion error", extra={"error": str(e)})
        error_message = (
            "I'm experiencing technical difficulties. For health emergencies, please call 108 or visit your nearest hospital."
        )
        return localize_text(error_message, target_lang=target_lang)


@app.get("/health")
async def health_check():
    return {
        "ok": True,
        "openai_configured": get_openai_client() is not None,
        "services": {
            "rag": True,
            "graph": ensure_neo4j(),
            "graph_fallback": True,
            "safety": True
        }
    }


@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...), lang: Optional[str] = None):
    """Convert speech to text using OpenAI Whisper"""
    if file.content_type and not file.content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Unsupported media type. Please upload an audio file.")

    try:
        audio_bytes = await file.read()
        transcript = transcribe_audio_bytes(audio_bytes, language_hint=lang)
        return {"text": transcript}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Speech-to-text processing failed")
        raise HTTPException(status_code=502, detail=f"STT error: {str(exc)}") from exc


def process_chat_request(request: ChatRequest) -> Tuple[ChatResponse, str, Dict[str, float]]:
    timings: Dict[str, float] = {}
    total_start = time.perf_counter()

    text = request.text
    requested_lang = request.lang if request.lang in SUPPORTED_LANG_CODES else None
    detected_lang = detect_language(text) if text else DEFAULT_LANG
    detected_supported = detected_lang if detected_lang in SUPPORTED_LANG_CODES else None
    target_lang = requested_lang or detected_supported or DEFAULT_LANG
    language_label = get_language_label(target_lang)

    profile: Profile = request.profile
    personalization_notes = build_personalization_notes(profile)

    processed_text = text
    source_lang_for_processing = detected_supported or DEFAULT_LANG
    if source_lang_for_processing != "en":
        processed_text = translate_text(text, target_lang="en", src_lang=source_lang_for_processing)

    safety_start = time.perf_counter()
    safety_result = detect_red_flags(processed_text, "en")
    mental_health_en = detect_mental_health_crisis(processed_text, "en")
    pregnancy_alert_en = detect_pregnancy_emergency(processed_text)
    timings["safety_analysis"] = time.perf_counter() - safety_start

    mental_health_display = mental_health_en
    if target_lang != "en" and mental_health_en["first_aid"]:
        mental_health_display = {
            **mental_health_en,
            "first_aid": localize_list(mental_health_en["first_aid"], target_lang),
        }

    pregnancy_guidance_display = (
        PREGNANCY_ALERT_GUIDANCE_EN
        if target_lang == "en"
        else localize_list(PREGNANCY_ALERT_GUIDANCE_EN, target_lang)
    )
    pregnancy_alert_display = {
        **pregnancy_alert_en,
        "guidance": pregnancy_guidance_display,
    }

    use_graph = is_graph_intent(processed_text)

    facts_en: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    answer = ""
    route = "vector"

    if safety_result["red_flag"]:
        symptoms = extract_symptoms(processed_text)
        red_flag_results = graph_get_red_flags(symptoms)
        if red_flag_results:
            facts_en.append({"type": "red_flags", "data": red_flag_results})

    if mental_health_en["crisis"]:
        facts_en.append(
            {
                "type": "mental_health_crisis",
                "data": {
                    "matched": mental_health_en["matched"],
                    "actions": mental_health_en["first_aid"],
                },
            }
        )

    if pregnancy_alert_en["concern"]:
        facts_en.append(
            {
                "type": "pregnancy_alert",
                "data": {
                    "matched": pregnancy_alert_en["matched"],
                    "guidance": PREGNANCY_ALERT_GUIDANCE_EN,
                },
            }
        )

    if use_graph:
        route = "graph"

        user_conditions: List[str] = []
        if profile.diabetes:
            user_conditions.append("Diabetes")
        if profile.hypertension:
            user_conditions.append("Hypertension")
        if profile.pregnancy:
            user_conditions.append("Pregnancy")

        condition_keywords = {
            "diabetes": "Diabetes",
            "hypertension": "Hypertension",
            "pregnancy": "Pregnancy",
            "pregnant": "Pregnancy",
        }
        processed_lower = processed_text.lower()
        for keyword, label in condition_keywords.items():
            if keyword in processed_lower and label not in user_conditions:
                user_conditions.append(label)

        if user_conditions:
            contras = graph_get_contraindications(user_conditions)
            if contras:
                condition_avoid_map: Dict[str, List[str]] = {}
                for entry in contras:
                    avoid_item = entry.get("avoid")
                    for cond in entry.get("because", []):
                        if cond in user_conditions and avoid_item:
                            condition_avoid_map.setdefault(cond, []).append(avoid_item)

                if condition_avoid_map:
                    facts_en.append(
                        {
                            "type": "contraindications",
                            "data": [
                                {
                                    "condition": cond,
                                    "avoid": sorted(set(items)),
                                }
                                for cond, items in condition_avoid_map.items()
                            ],
                        }
                    )

            safe_actions_map: Dict[str, List[str]] = {}
            for condition in user_conditions:
                safe_entries = graph_get_safe_actions([condition])
                actions = sorted(
                    {
                        entry.get("safeAction")
                        for entry in safe_entries
                        if entry.get("safeAction")
                    }
                )
                if actions:
                    safe_actions_map[condition] = actions

            if safe_actions_map:
                facts_en.append(
                    {
                        "type": "safe_actions",
                        "data": [
                            {"condition": cond, "actions": actions}
                            for cond, actions in safe_actions_map.items()
                        ],
                    }
                )

        city = profile.city or extract_city(processed_text)
        if city:
            providers = graph_get_providers(city)
            if providers:
                facts_en.append({"type": "providers", "data": providers})

        rag_start = time.perf_counter()
        rag_results = retrieve(processed_text, k=3)
        timings["retrieval"] = time.perf_counter() - rag_start
        context = "\n\n".join([r["chunk"] for r in rag_results])
        citations = [
            {"source": r["source"], "id": r["id"], "topic": r.get("topic")}
            for r in rag_results
        ]

        if facts_en:
            fact_summary = "\n\nRelevant facts from database:\n"
            for fact_group in facts_en:
                if fact_group["type"] == "red_flags":
                    fact_summary += "⚠️ Red flag conditions detected\n"
                elif fact_group["type"] == "contraindications":
                    avoid_phrases = []
                    for entry in fact_group["data"]:
                        avoid_items = ", ".join(entry["avoid"])
                        avoid_phrases.append(f"{entry['condition']}: {avoid_items}")
                    if avoid_phrases:
                        fact_summary += f"⛔ Things to avoid — {'; '.join(avoid_phrases)}\n"
                elif fact_group["type"] == "providers":
                    fact_summary += f"🏥 {len(fact_group['data'])} healthcare providers found\n"
            context += fact_summary

        if personalization_notes:
            context += "\n\nPersonalization notes:\n" + "\n".join(
                f"- {note}" for note in personalization_notes
            )
            if not any(f.get("type") == "personalization" for f in facts_en):
                facts_en.append({"type": "personalization", "data": personalization_notes})

        generation_start = time.perf_counter()
        answer = generate_answer(
            context=context,
            query_en=processed_text,
            target_lang=target_lang,
            language_label=language_label,
            original_query=text,
            facts=facts_en,
            citations=citations,
        )
        timings["answer_generation"] = time.perf_counter() - generation_start

    else:
        rag_start = time.perf_counter()
        rag_results = retrieve(processed_text, k=4)
        timings["retrieval"] = time.perf_counter() - rag_start
        if not rag_results:
            answer = localize_text(
                "I don't have specific information about that. For health concerns, please consult a healthcare professional.",
                target_lang=target_lang,
            )
        else:
            context = "\n\n".join([r["chunk"] for r in rag_results])
            citations = [
                {"source": r["source"], "id": r["id"], "topic": r.get("topic")}
                for r in rag_results
            ]

            personalized_conditions: List[str] = []
            if profile.diabetes:
                personalized_conditions.append("diabetes")
            if profile.hypertension:
                personalized_conditions.append("hypertension")
            if profile.pregnancy:
                personalized_conditions.append("pregnancy")
            if personalized_conditions:
                context += (
                    "\n\nNote: User has "
                    + " and ".join(personalized_conditions)
                    + ". Provide relevant precautions."
                )

            if personalization_notes:
                context += "\n\nPersonalization notes:\n" + "\n".join(
                    f"- {note}" for note in personalization_notes
                )
                facts_en.append({"type": "personalization", "data": personalization_notes})

            generation_start = time.perf_counter()
            answer = generate_answer(
                context=context,
                query_en=processed_text,
                target_lang=target_lang,
                language_label=language_label,
                original_query=text,
                facts=facts_en,
                citations=citations,
            )
            timings["answer_generation"] = time.perf_counter() - generation_start

    if not safety_result["red_flag"]:
        answer += "\n\n" + get_localized_disclaimer(target_lang)

    facts_response = localize_fact_guidance(facts_en, target_lang)

    safety_payload = {
        **safety_result,
        "mental_health": mental_health_display,
        "pregnancy": pregnancy_alert_display,
    }

    response = ChatResponse(
        answer=answer,
        route=route,
        facts=facts_response,
        citations=citations,
        safety=safety_payload,
    )
    logger.debug(
        "Chat response composed",
        extra={"route": route, "facts": len(response.facts), "target_lang": target_lang},
    )
    timings["total"] = time.perf_counter() - total_start
    return response, target_lang, timings


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with routing, safety detection, and RAG
    """
    logger.info(
        "Received chat request",
        extra={
            "lang": request.lang,
            "profile": request.profile.model_dump(exclude_none=True),
        },
    )
    try:
        response, target_lang, timings = process_chat_request(request)
        logger.info(
            "Chat response ready",
            extra={
                "route": response.route,
                "request_lang": request.lang,
                "target_lang": target_lang,
                "facts": len(response.facts),
                "timings": timings,
            },
        )
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat processing failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process your request right now. Please try again in a moment.",
        ) from exc


@app.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    lang: Optional[str] = Form(None),
    profile: Optional[str] = Form(None),
):
    """
    Voice-first endpoint: audio -> Whisper STT -> chat -> TTS audio response
    """
    if audio.content_type and not audio.content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Unsupported media type. Please upload an audio file.")

    try:
        audio_bytes = await audio.read()
        stt_start = time.perf_counter()
        transcript = transcribe_audio_bytes(audio_bytes, language_hint=lang)
        stt_duration = time.perf_counter() - stt_start

        profile_payload: Dict[str, Any] = {}
        if profile:
            try:
                profile_payload = json.loads(profile)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail=f"Invalid profile JSON: {exc}") from exc

        chat_request = ChatRequest(
            text=transcript,
            lang=lang or DEFAULT_LANG,
            profile=Profile(**profile_payload),
        )

        chat_response, target_lang, chat_timings = process_chat_request(chat_request)

        tts_start = time.perf_counter()
        audio_bytes_out, tts_provider, audio_mime = synthesize_speech(chat_response.answer, target_lang)
        tts_duration = time.perf_counter() - tts_start

        metadata = {
            "timings": {
                **chat_timings,
                "stt": stt_duration,
                "tts": tts_duration,
            },
            "tts_provider": tts_provider,
            "audio_mime": audio_mime,
            "transcript_length": len(transcript),
            "audio_input_bytes": len(audio_bytes),
            "audio_output_bytes": len(audio_bytes_out),
        }

        return VoiceChatResponse(
            transcript=transcript,
            answer=chat_response.answer,
            audio_base64=encode_audio_base64(audio_bytes_out),
            route=chat_response.route,
            facts=chat_response.facts,
            citations=chat_response.citations,
            safety=chat_response.safety,
            metadata=metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Voice chat processing failed")
        raise HTTPException(
            status_code=500,
            detail="Voice processing failed. Please try again later.",
        ) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)