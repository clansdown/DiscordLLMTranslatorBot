"""Discord bot setup and main loop."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import TYPE_CHECKING

import discord
from discord import Intents
from discord.ext.commands import Bot

from discord_llm_translator.config import BotConfig
from discord_llm_translator.cogs.translation import TranslationHandler
from discord_llm_translator.services.language_detector import LanguageDetector
from discord_llm_translator.services.openrouter_client import OpenRouterClient
from discord_llm_translator.utils.formatting import get_language_name

if TYPE_CHECKING:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class DiscordTranslatorBot:
    """Main Discord bot class for translation functionality."""

    def __init__(self, config: BotConfig) -> None:
        """Initialize the bot with configuration."""
        self._config = config
        self._intents = Intents.default()
        self._intents.message_content = True
        self._client = Bot(intents=self._intents, command_prefix="")
        self._openrouter_client: OpenRouterClient | None = None
        self._language_detector: LanguageDetector | None = None
        self._translation_handler: TranslationHandler | None = None
        self._ready_event = asyncio.Event()

    async def setup(self) -> None:
        """Set up bot components."""
        logger.info("Setting up bot components...")

        self._openrouter_client = OpenRouterClient(
            api_key=self._config.openrouter_api_key,
            model=self._config.model,
        )

        self._language_detector = LanguageDetector(
            confidence_threshold=self._config.language_confidence_threshold,
        )

        self._translation_handler = TranslationHandler(
            client=self._client,
            config=self._config,
            openrouter_client=self._openrouter_client,
            language_detector=self._language_detector,
        )

        self._client.add_listener(self._on_ready, "on_ready")
        self._client.add_listener(self._translation_handler.on_message, "on_message")

        self._log_configuration()

        logger.info("Bot setup complete")

    def _log_configuration(self) -> None:
        """Log the current configuration at startup."""
        root_logger = logging.getLogger()
        log_level = logging.getLevelName(root_logger.getEffectiveLevel())
        logger.info(f"Log level: {log_level}")

        logger.info(f"Model: {self._config.model}")
        logger.info(f"Rate limit: {self._config.rate_limit_per_user_seconds} seconds per user")

        if self._config.reply_channels:
            logger.info("Reply channels:")
            for channel_config in self._config.reply_channels:
                lang_name = get_language_name(channel_config.default_language)
                logger.info(f"  Channel {channel_config.channel_id} → {lang_name} ({channel_config.default_language})")
        else:
            logger.info("No reply channels configured")

        if self._config.sync_groups:
            logger.info("Sync groups:")
            for group in self._config.sync_groups:
                channel_list = ", ".join(
                    f"#{config.channel_id} ({config.language})"
                    for config in group.channels
                )
                logger.info(f"  {group.name}: {channel_list}")
        else:
            logger.info("No sync groups configured")

    async def _on_ready(self) -> None:
        """Called when the bot is ready and connected."""
        logger.info(f"Bot connected as {self._client.user}")
        self._ready_event.set()

    async def start(self) -> None:
        """Start the bot and connect to Discord."""
        await self.setup()
        logger.info("Starting bot...")
        await self._client.start(self._config.discord_token)

    async def shutdown(self) -> None:
        """Gracefully shut down the bot."""
        logger.info("Shutting down bot...")

        if self._openrouter_client is not None:
            await self._openrouter_client.close()

        await self._client.close()
        logger.info("Bot shutdown complete")

    @property
    def ready_event(self) -> asyncio.Event:
        """Event that fires when bot is ready."""
        return self._ready_event
