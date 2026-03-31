"""Discord message formatting utilities."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Member, User


def format_translation_message(
    original_author: str,
    detected_language: str,
    prefix_template: str,
) -> str:
    """
    Format the prefix for a translation message.

    Args:
        original_author: Display name or mention of the original message author.
        detected_language: Human-readable name of the detected source language.
        prefix_template: Template string with {author} and {language} placeholders.

    Returns:
        Formatted prefix string.
    """
    return prefix_template.format(
        author=original_author,
        language=detected_language,
    )


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding a suffix if truncated.

    Args:
        text: The text to truncate.
        max_length: Maximum length including suffix.
        suffix: String to append if truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text

    truncated_length = max_length - len(suffix)
    if truncated_length <= 0:
        return suffix[:max_length]

    return text[:truncated_length] + suffix


LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "pl": "Polish",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "el": "Greek",
    "he": "Hebrew",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "cs": "Czech",
    "sk": "Slovak",
    "hu": "Hungarian",
    "ro": "Romanian",
    "uk": "Ukrainian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sr": "Serbian",
    "sl": "Slovenian",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
}


def get_language_name(language_code: str) -> str:
    """
    Get the human-readable name for a language code.

    Args:
        language_code: ISO 639-1 language code.

    Returns:
        Human-readable language name, or the code if unknown.
    """
    return LANGUAGE_NAMES.get(language_code.lower(), language_code.upper())
