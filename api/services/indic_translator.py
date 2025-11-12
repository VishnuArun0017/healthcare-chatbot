import logging
import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class IndicTranslationResult:
    success: bool
    translated_text: Optional[str]
    native_script: Optional[str]
    provider: str
    details: Dict[str, str]


class IndicTransService:
    """
    Lazy wrapper around IndicTrans2 models exposed via HuggingFace `transformers`.

    The service is entirely optional – if the dependencies or HuggingFace credentials
    are missing, calls will fall back to the legacy Google translator path.
    """

    _FLORES_MAP: Dict[str, str] = {
        "hi": "hin_Deva",
        "ta": "tam_Taml",
        "te": "tel_Telu",
        "kn": "kan_Knda",
        "ml": "mal_Mlym",
    }

    def __init__(self) -> None:
        self._logger = logging.getLogger("health_assistant.indictrans")
        self._model_id_indic_en = os.getenv(
            "INDIC_TRANS_MODEL_INDIC_EN", "ai4bharat/indictrans2-indic-en-dist-200M"
        )
        self._model_id_en_indic = os.getenv(
            "INDIC_TRANS_MODEL_EN_INDIC", "ai4bharat/indictrans2-en-indic-dist-200M"
        )
        self._hf_token = (
            os.getenv("INDIC_TRANS_HF_TOKEN")
            or os.getenv("HF_TOKEN")
            or os.getenv("HUGGINGFACE_TOKEN")
            or os.getenv("TRANS_HF_TOKEN")
        )
        self._lock = threading.Lock()
        self._service_disabled = False

        self._processor = None
        self._torch = None
        self._device = None
        self._processor_ready = False

        self._tokenizer_indic_en = None
        self._model_indic_en = None
        self._indic_en_ready = False
        self._indic_en_disabled = False
        self._indic_en_error: Optional[str] = None

        self._tokenizer_en_indic = None
        self._model_en_indic = None
        self._en_indic_ready = False
        self._en_indic_disabled = False
        self._en_indic_error: Optional[str] = None

    def is_enabled(self) -> bool:
        """
        Returns True if the service is available (or might still become available)
        """
        return not self._service_disabled

    def translate_romanized_to_english(self, text: str, lang: str) -> IndicTranslationResult:
        """
        Attempt to translate romanised Indic text to English using IndicTrans2.
        """
        flores_code = self._FLORES_MAP.get(lang)
        if not flores_code:
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={"reason": f"unsupported_language:{lang}"},
            )

        if not self._ensure_processor():
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={
                    "reason": "processor_initialization_failed",
                },
            )

        if not self._ensure_indic_en_model():
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={
                    "reason": "model_initialization_failed",
                    "error": self._indic_en_error or "",
                },
            )

        assert self._processor is not None
        assert self._tokenizer_indic_en is not None
        assert self._model_indic_en is not None
        assert self._torch is not None
        assert self._device is not None

        try:
            processed_batch = self._processor.preprocess_batch(
                [text], src_lang=flores_code, tgt_lang="eng_Latn"
            )
            if not processed_batch:
                return IndicTranslationResult(
                    success=False,
                    translated_text=None,
                    native_script=None,
                    provider="indictrans2",
                    details={"reason": "empty_preprocess"},
                )

            inputs = self._tokenizer_indic_en(
                processed_batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
            ).to(self._device)

            with self._torch.no_grad():
                outputs = self._model_indic_en.generate(
                    **inputs,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                )

            decoded = self._tokenizer_indic_en.batch_decode(outputs, skip_special_tokens=True)
            postprocessed = self._processor.postprocess_batch(
                decoded, src_lang=flores_code, tgt_lang="eng_Latn"
            )

            english_text = postprocessed[0] if postprocessed else decoded[0]
            return IndicTranslationResult(
                success=bool(english_text),
                translated_text=english_text,
                native_script=None,
                provider="indictrans2",
                details={"model": self._model_id_indic_en},
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.warning(
                "IndicTrans2 translation failed",
                extra={"error": str(exc), "language": lang},
            )
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={"reason": "exception", "error": str(exc)},
            )

    def translate_english_to_local(self, text: str, lang: str) -> IndicTranslationResult:
        """
        Translate English text to Indic languages using IndicTrans2.
        """
        flores_code = self._FLORES_MAP.get(lang)
        if not flores_code:
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={"reason": f"unsupported_language:{lang}"},
            )

        if not self._ensure_processor():
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={"reason": "processor_initialization_failed"},
            )

        if not self._ensure_en_indic_model():
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={
                    "reason": "model_initialization_failed",
                    "error": self._en_indic_error or "",
                },
            )

        assert self._processor is not None
        assert self._tokenizer_en_indic is not None
        assert self._model_en_indic is not None
        assert self._torch is not None
        assert self._device is not None

        try:
            processed_batch = self._processor.preprocess_batch(
                [text], src_lang="eng_Latn", tgt_lang=flores_code
            )
            if not processed_batch:
                return IndicTranslationResult(
                    success=False,
                    translated_text=None,
                    native_script=None,
                    provider="indictrans2",
                    details={"reason": "empty_preprocess"},
                )

            inputs = self._tokenizer_en_indic(
                processed_batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
            ).to(self._device)

            with self._torch.no_grad():
                outputs = self._model_en_indic.generate(
                    **inputs,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                )

            decoded = self._tokenizer_en_indic.batch_decode(outputs, skip_special_tokens=True)
            postprocessed = self._processor.postprocess_batch(
                decoded, src_lang="eng_Latn", tgt_lang=flores_code
            )

            localized = postprocessed[0] if postprocessed else decoded[0]
            return IndicTranslationResult(
                success=bool(localized),
                translated_text=localized,
                native_script=localized,
                provider="indictrans2",
                details={"model": self._model_id_en_indic},
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.warning(
                "IndicTrans2 localization failed",
                extra={"error": str(exc), "language": lang},
            )
            return IndicTranslationResult(
                success=False,
                translated_text=None,
                native_script=None,
                provider="indictrans2",
                details={"reason": "exception", "error": str(exc)},
            )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_processor(self) -> bool:
        if self._service_disabled:
            return False

        if self._processor_ready:
            return True

        with self._lock:
            if self._processor_ready or self._service_disabled:
                return self._processor_ready

            try:
                from IndicTransToolkit import IndicProcessor  # type: ignore
                import torch  # type: ignore
            except Exception as exc:  # pragma: no cover - import guard
                self._logger.info(
                    "IndicTrans2 dependencies missing; leaving service disabled",
                    extra={"error": str(exc)},
                )
                self._service_disabled = True
                return False

            try:
                self._torch = torch
                self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self._processor = IndicProcessor(inference=True)
                self._processor_ready = True
                self._logger.info(
                    "IndicTrans2 processor initialised",
                    extra={"device": str(self._device)},
                )
            except Exception as exc:  # pragma: no cover
                self._logger.warning(
                    "IndicTrans2 processor initialisation failed",
                    extra={"error": str(exc)},
                )
                self._service_disabled = True
                return False

        return self._processor_ready

    def _ensure_indic_en_model(self) -> bool:
        if self._indic_en_disabled:
            return False
        if self._indic_en_ready:
            return True

        if not self._ensure_processor():
            self._indic_en_disabled = True
            return False

        if not self._model_id_indic_en:
            self._logger.info(
                "IndicTrans2 Indic->English model id not configured; disabling direction"
            )
            self._indic_en_error = "model_id_missing"
            self._indic_en_disabled = True
            return False

        with self._lock:
            if self._indic_en_ready or self._indic_en_disabled:
                return self._indic_en_ready
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore
            except Exception as exc:  # pragma: no cover
                self._logger.info(
                    "Transformers missing for IndicTrans2 Indic→English",
                    extra={"error": str(exc)},
                )
                self._indic_en_disabled = True
                return False

            try:
                kwargs = self._build_auth_kwargs()
                tokenizer = AutoTokenizer.from_pretrained(self._model_id_indic_en, **kwargs)
                model = AutoModelForSeq2SeqLM.from_pretrained(self._model_id_indic_en, **kwargs)
                model.to(self._device)
                self._tokenizer_indic_en = tokenizer
                self._model_indic_en = model
                self._indic_en_ready = True
                self._indic_en_error = None
                self._logger.info(
                    "IndicTrans2 Indic->English model loaded",
                    extra={
                        "model": self._model_id_indic_en,
                        "device": str(self._device),
                        "uses_token": bool(self._hf_token),
                    },
                )
            except Exception as exc:  # pragma: no cover
                error_msg = str(exc)
                self._logger.warning(
                    "Failed to load IndicTrans2 Indic->English model",
                    extra={"error": error_msg, "model": self._model_id_indic_en},
                )
                self._indic_en_error = error_msg
                self._indic_en_disabled = True
                return False

        return self._indic_en_ready

    def _ensure_en_indic_model(self) -> bool:
        if self._en_indic_disabled:
            return False
        if self._en_indic_ready:
            return True

        if not self._ensure_processor():
            self._en_indic_disabled = True
            return False

        if not self._model_id_en_indic:
            self._logger.info(
                "IndicTrans2 English->Indic model id not configured; disabling direction"
            )
            self._en_indic_error = "model_id_missing"
            self._en_indic_disabled = True
            return False

        with self._lock:
            if self._en_indic_ready or self._en_indic_disabled:
                return self._en_indic_ready
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore
            except Exception as exc:  # pragma: no cover
                self._logger.info(
                    "Transformers missing for IndicTrans2 English→Indic",
                    extra={"error": str(exc)},
                )
                self._en_indic_disabled = True
                return False

            try:
                kwargs = self._build_auth_kwargs()
                tokenizer = AutoTokenizer.from_pretrained(self._model_id_en_indic, **kwargs)
                model = AutoModelForSeq2SeqLM.from_pretrained(self._model_id_en_indic, **kwargs)
                model.to(self._device)
                self._tokenizer_en_indic = tokenizer
                self._model_en_indic = model
                self._en_indic_ready = True
                self._en_indic_error = None
                self._logger.info(
                    "IndicTrans2 English->Indic model loaded",
                    extra={
                        "model": self._model_id_en_indic,
                        "device": str(self._device),
                        "uses_token": bool(self._hf_token),
                    },
                )
            except Exception as exc:  # pragma: no cover
                error_msg = str(exc)
                self._logger.warning(
                    "Failed to load IndicTrans2 English->Indic model",
                    extra={"error": error_msg, "model": self._model_id_en_indic},
                )
                self._en_indic_error = error_msg
                self._en_indic_disabled = True
                return False

        return self._en_indic_ready

    def _build_auth_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"trust_remote_code": True}
        if self._hf_token:
            kwargs["token"] = self._hf_token
        return kwargs


