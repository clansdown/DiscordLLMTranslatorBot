"""Translation event handlers for Discord message processing."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import discord

from discord_llm_translator.config import (
    BotConfig,
    ReplyChannelConfig,
    SyncChannelConfig,
    SyncGroupConfig,
)
from discord_llm_translator.models.translation import TranslationRequest
from discord_llm_translator.services.language_detector import LanguageDetector
from discord_llm_translator.services.openrouter_client import OpenRouterClient
from discord_llm_translator.utils.formatting import (
    format_translation_message,
    get_language_name,
    truncate_text,
)

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Simple rate limiter for per-user translation requests."""

    per_user_seconds: int
    last_request: dict[int, datetime]

    def is_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed to make a request."""
        now = datetime.now()
        last = self.last_request.get(user_id)
        if last is None:
            return True
        elapsed = (now - last).total_seconds()
        return elapsed >= self.per_user_seconds

    def record_request(self, user_id: int) -> None:
        """Record a request for rate limiting."""
        self.last_request[user_id] = datetime.now()


class TranslationHandler:
    """Handler for translation-related Discord events."""

    def __init__(
        self,
        client: discord.Client,
        config: BotConfig,
        openrouter_client: OpenRouterClient,
        language_detector: LanguageDetector,
    ) -> None:
        """Initialize the translation handler."""
        self._client = client
        self._config = config
        self._openrouter_client = openrouter_client
        self._language_detector = language_detector
        self._rate_limiter = RateLimiter(
            per_user_seconds=config.rate_limit_per_user_seconds,
            last_request={},
        )
        self._processed_messages: set[int] = set()
        self._lock = asyncio.Lock()

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages."""
        if message.author.bot and not self._config.translate_bot_messages:
            return

        if message.webhook_id is not None and not self._config.translate_webhook_messages:
            return

        if not message.content or not message.content.strip():
            return

        reply_config = self._config.get_reply_channel_config(message.channel.id)
        if reply_config is not None:
            await self._handle_reply_mode(message, reply_config)
            return

        sync_result = self._config.get_sync_channel_config(message.channel.id)
        if sync_result is not None:
            await self._handle_sync_mode(message, sync_result[0], sync_result[1])

    async def _handle_reply_mode(
        self,
        message: discord.Message,
        channel_config: ReplyChannelConfig,
    ) -> None:
        """Handle message in reply mode channel."""
        if not self._rate_limiter.is_allowed(message.author.id):
            return

        try:
            detection_result = self._language_detector.detect(message.content)
        except ValueError as e:
            logger.debug(f"Language detection failed for message {message.id}: {e}")
            return

        if detection_result.language == channel_config.default_language:
            return

        self._rate_limiter.record_request(message.author.id)

        text_to_translate = message.content
        if self._config.max_chars > 0:
            text_to_translate = truncate_text(text_to_translate, self._config.max_chars)

        system_prompt = self._config.get_system_prompt_for_channel(message.channel.id)

        request = TranslationRequest(
            text=text_to_translate,
            source_language=detection_result.language,
            target_language=channel_config.default_language,
            system_prompt=system_prompt,
        )

        try:
            result = await self._openrouter_client.translate(request)
        except Exception as e:
            logger.error(f"Translation failed for message {message.id}: {e}")
            return

        await self._send_translation_reply(
            message=message,
            translated_text=result.translated_text,
            detected_language=get_language_name(detection_result.language),
            author_name=message.author.display_name,
        )

    async def _handle_sync_mode(
        self,
        message: discord.Message,
        group_config: SyncGroupConfig,
        source_channel_config: SyncChannelConfig,
    ) -> None:
        """Handle message in sync mode channel."""
        async with self._lock:
            if message.id in self._processed_messages:
                return
            self._processed_messages.add(message.id)

        if len(self._processed_messages) > 1000:
            async with self._lock:
                self._processed_messages = set(list(self._processed_messages)[-500:])

        if not self._rate_limiter.is_allowed(message.author.id):
            return

        text_to_translate = message.content
        if self._config.max_chars > 0:
            text_to_translate = truncate_text(text_to_translate, self._config.max_chars)

        system_prompt = self._config.get_system_prompt_for_channel(message.channel.id)

        tasks: list[Awaitable[None]] = []

        for target_channel_config in group_config.channels:
            if target_channel_config.channel_id == source_channel_config.channel_id:
                continue

            request = TranslationRequest(
                text=text_to_translate,
                source_language=source_channel_config.language,
                target_language=target_channel_config.language,
                system_prompt=system_prompt,
            )

            task = self._translate_and_send(
                message=message,
                target_channel_id=target_channel_config.channel_id,
                translation_request=request,
            )
            tasks.append(task)

        if tasks:
            self._rate_limiter.record_request(message.author.id)
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _translate_and_send(
        self,
        message: discord.Message,
        target_channel_id: int,
        translation_request: TranslationRequest,
    ) -> None:
        """Translate a message and send it to a target channel."""
        try:
            result = await self._openrouter_client.translate(translation_request)

            target_channel = self._client.get_channel(target_channel_id)
            if not isinstance(target_channel, discord.TextChannel):
                logger.warning(f"Target channel {target_channel_id} not found or not a text channel")
                return

            translated_text = f"**[{message.author.display_name}] {result.translated_text}**"
            await target_channel.send(translated_text)

        except Exception as e:
            logger.error(
                f"Failed to translate message {message.id} to channel "
                f"{target_channel_id}: {e}"
            )

    async def _send_translation_reply(
        self,
        message: discord.Message,
        translated_text: str,
        detected_language: str,
        author_name: str,
    ) -> None:
        """Send a translation as a reply to a message."""
        if self._config.translation_prefix:
            prefix = format_translation_message(
                original_author=author_name,
                detected_language=detected_language,
                prefix_template=self._config.translation_prefix,
            )
            reply_content = f"{prefix}\n\n{translated_text}"
        else:
            reply_content = translated_text

        try:
            await message.reply(reply_content, mention_author=False)
        except discord.DiscordException as e:
            logger.error(f"Failed to send translation reply: {e}")
