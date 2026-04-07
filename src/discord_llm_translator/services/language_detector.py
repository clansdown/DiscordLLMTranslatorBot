"""Language detection service using langdetect."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from langdetect import LangDetectException, detect_langs

from discord_llm_translator.models.translation import LanguageDetectionResult

if TYPE_CHECKING:
    pass


class LanguageDetector:
    """Wrapper around langdetect with caching and confidence threshold support."""

    def __init__(self, confidence_threshold: float = 0.7) -> None:
        """
        Initialize the language detector.

        Args:
            confidence_threshold: Minimum confidence required to return a result.
                                 Lower confidence detections will raise an error.
        """
        self._confidence_threshold = confidence_threshold

    def detect(self, text: str) -> LanguageDetectionResult:
        """
        Detect the language of the given text.

        Args:
            text: The text to analyze.

        Returns:
            LanguageDetectionResult with detected language and confidence.

        Raises:
            ValueError: If text is empty or confidence is below threshold.
        """
        if not text or not text.strip():
            raise ValueError("Cannot detect language of empty text")

        try:
            detected_languages = detect_langs(text)
        except LangDetectException as e:
            raise ValueError(f"Language detection failed: {e}") from e

        if not detected_languages:
            raise ValueError("No language detected")

        top_result = detected_languages[0]
        detected_language = top_result.lang
        confidence = top_result.prob

        if confidence < self._confidence_threshold:
            raise ValueError(
                f"Language detection confidence ({confidence:.2f}) below threshold "
                f"({self._confidence_threshold:.2f})"
            )

        return LanguageDetectionResult(
            language=detected_language,
            confidence=confidence,
        )

    def is_language(self, text: str, language_code: str) -> bool:
        """
        Check if the given text is in the specified language.

        Args:
            text: The text to check.
            language_code: The ISO 639-1 language code to check against.

        Returns:
            True if the text is in the specified language, False otherwise.
        """
        try:
            result = self.detect(text)
            return result.language == language_code
        except ValueError:
            return False


@lru_cache(maxsize=1024)
def _cached_detect_language(text: str) -> tuple[str, float]:
    """
    Cached language detection for repeated texts.

    Args:
        text: The text to analyze (must be hashable).

    Returns:
        Tuple of (language_code, confidence).
    """
    try:
        detected_languages = detect_langs(text)
        if detected_languages:
            top = detected_languages[0]
            return (top.lang, top.prob)
    except LangDetectException:
        pass
    return ("unknown", 0.0)


def detect_language_quick(text: str) -> LanguageDetectionResult:
    """
    Quick language detection with caching for performance.

    Use this for high-volume detection where exact confidence isn't critical.

    Args:
        text: The text to analyze.

    Returns:
        LanguageDetectionResult with detected language and confidence.
    """
    language, confidence = _cached_detect_language(text)
    return LanguageDetectionResult(language=language, confidence=confidence)
