"""Application constants and default values."""

DEFAULT_SYSTEM_PROMPT = (
    "Translate the following text from {source_language} to {target_language}. "
    "Preserve the original formatting, tone, and style as closely as possible. "
    "Only output the translation, nothing else."
)

DEFAULT_MAX_CHARS = 10000
DEFAULT_RATE_LIMIT_SECONDS = 3
DEFAULT_LANGUAGE_CONFIDENCE_THRESHOLD = 0.7
DEFAULT_TRANSLATION_PREFIX = "**[{author}] Translated from {language}:**"
DEFAULT_TRANSLATE_BOT_MESSAGES = False
DEFAULT_TRANSLATE_WEBHOOK_MESSAGES = False

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

ZDR_POLICY_REFERER = "https://openrouter.ai/docs/zdr"
ZDR_POLICY_SITE = "https://openrouter.ai"
