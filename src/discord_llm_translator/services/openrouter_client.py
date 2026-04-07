"""OpenRouter API client for LLM-based translation."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from discord_llm_translator.constants import (
    OPENROUTER_API_URL,
    ZDR_POLICY_REFERER,
)
from discord_llm_translator.models.translation import (
    TranslationRequest,
    TranslationResult,
)
from discord_llm_translator.utils.formatting import get_language_name


class OpenRouterError(Exception):
    """Base exception for OpenRouter API errors."""

    pass


class OpenRouterAPIError(OpenRouterError):
    """Exception for API-level errors (non-2xx responses)."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"OpenRouter API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class OpenRouterRateLimitError(OpenRouterError):
    """Exception for rate limiting errors."""

    pass


class OpenRouterClient:
    """Async client for the OpenRouter API with ZDR policy headers."""

    def __init__(
        self,
        api_key: str,
        model: str = "google/gemini-2.5-flash",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """
        Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key.
            model: Model identifier to use for translations.
            max_retries: Maximum number of retries on failure.
            retry_delay: Base delay between retries (exponential backoff).
        """
        self._api_key = api_key
        self._model = model
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        Translate text using the OpenRouter API.

        Args:
            request: Translation request with text and language info.

        Returns:
            TranslationResult with the translated text.

        Raises:
            OpenRouterError: If the API request fails.
            OpenRouterRateLimitError: If rate limited.
        """
        system_prompt = request.system_prompt.format(
            source_language=get_language_name(request.source_language),
            target_language=get_language_name(request.target_language),
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.text},
        ]

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": 4096,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": ZDR_POLICY_REFERER,
            "X-Title": "Discord LLM Translator Bot",
        }

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return await self._make_request(headers, payload)
            except OpenRouterRateLimitError:
                raise
            except OpenRouterError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2**attempt))

        if last_error is not None:
            raise OpenRouterError(f"Translation failed after {self._max_retries} retries") from last_error

        raise OpenRouterError("Translation failed with unknown error")

    async def _make_request(
        self,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> TranslationResult:
        """Make a single request to the OpenRouter API."""
        session = await self._get_session()

        try:
            async with session.post(
                OPENROUTER_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status == 429:
                    raise OpenRouterRateLimitError("Rate limited by OpenRouter API")

                if response.status != 200:
                    error_body = await response.text()
                    raise OpenRouterAPIError(response.status, error_body)

                data = await response.json()

        except aiohttp.ClientError as e:
            raise OpenRouterError(f"Network error: {e}") from e

        return self._parse_response(data)

    def _parse_response(self, data: dict[str, Any]) -> TranslationResult:
        """Parse the API response into a TranslationResult."""
        try:
            choices = data.get("choices", [])
            if not choices:
                raise OpenRouterError("No choices in API response")

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                raise OpenRouterError("Empty content in API response")

            return TranslationResult(
                original_text="",
                translated_text=content.strip(),
                source_language="",
                target_language="",
            )

        except (KeyError, IndexError) as e:
            raise OpenRouterError(f"Failed to parse API response: {e}") from e
