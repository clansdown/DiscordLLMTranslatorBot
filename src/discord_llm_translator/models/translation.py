"""Data models for translation operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageDetectionResult:
    """The result of language detection."""

    language: str
    confidence: float


@dataclass(frozen=True)
class TranslationRequest:
    """A request to translate text from one language to another."""

    text: str
    source_language: str
    target_language: str
    system_prompt: str


@dataclass(frozen=True)
class TranslationResult:
    """The result of a translation request."""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
