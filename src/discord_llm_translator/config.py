"""Configuration dataclasses and loading."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import tomli

from discord_llm_translator.constants import (
    DEFAULT_LANGUAGE_CONFIDENCE_THRESHOLD,
    DEFAULT_MAX_CHARS,
    DEFAULT_RATE_LIMIT_SECONDS,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TRANSLATE_BOT_MESSAGES,
    DEFAULT_TRANSLATE_WEBHOOK_MESSAGES,
    DEFAULT_TRANSLATION_PREFIX,
)


@dataclass(frozen=True)
class SyncChannelConfig:
    """Configuration for a single channel within a sync group."""

    channel_id: int
    language: str


@dataclass(frozen=True)
class SyncGroupConfig:
    """Configuration for a group of synced channels."""

    name: str
    channels: tuple[SyncChannelConfig, ...]
    system_prompt: str | None = None


@dataclass(frozen=True)
class ReplyChannelConfig:
    """Configuration for a reply-mode channel."""

    channel_id: int
    default_language: str
    system_prompt: str | None = None


@dataclass
class BotConfig:
    """Main bot configuration container."""

    discord_token: str
    openrouter_api_key: str
    model: str
    system_prompt: str
    max_chars: int
    rate_limit_per_user_seconds: int
    language_confidence_threshold: float
    translation_prefix: str
    translate_bot_messages: bool
    translate_webhook_messages: bool
    reply_channels: tuple[ReplyChannelConfig, ...] = field(default_factory=tuple)
    sync_groups: tuple[SyncGroupConfig, ...] = field(default_factory=tuple)

    @classmethod
    def from_file(cls, file_path: Path) -> BotConfig:
        """Load configuration from a TOML file."""
        with file_path.open("rb") as f:
            raw_config = tomli.load(f)

        discord_token = cls._get_string_or_env(
            raw_config, "discord_token", "DISCORD_TOKEN"
        )
        openrouter_api_key = cls._get_string_or_env(
            raw_config, "openrouter_api_key", "OPENROUTER_API_KEY"
        )

        if not discord_token:
            raise ValueError("discord_token is required (set in config or DISCORD_TOKEN env var)")
        if not openrouter_api_key:
            raise ValueError(
                "openrouter_api_key is required (set in config or OPENROUTER_API_KEY env var)"
            )

        model = raw_config.get("model", "google/gemini-2.5-flash")
        system_prompt = raw_config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        max_chars = raw_config.get("max_chars", DEFAULT_MAX_CHARS)
        rate_limit_per_user_seconds = raw_config.get(
            "rate_limit_per_user_seconds", DEFAULT_RATE_LIMIT_SECONDS
        )
        language_confidence_threshold = raw_config.get(
            "language_confidence_threshold", DEFAULT_LANGUAGE_CONFIDENCE_THRESHOLD
        )
        translation_prefix = raw_config.get("translation_prefix", DEFAULT_TRANSLATION_PREFIX)
        translate_bot_messages = raw_config.get(
            "translate_bot_messages", DEFAULT_TRANSLATE_BOT_MESSAGES
        )
        translate_webhook_messages = raw_config.get(
            "translate_webhook_messages", DEFAULT_TRANSLATE_WEBHOOK_MESSAGES
        )

        reply_channels = cls._parse_reply_channels(raw_config)
        sync_groups = cls._parse_sync_groups(raw_config)

        return cls(
            discord_token=discord_token,
            openrouter_api_key=openrouter_api_key,
            model=model,
            system_prompt=system_prompt,
            max_chars=max_chars,
            rate_limit_per_user_seconds=rate_limit_per_user_seconds,
            language_confidence_threshold=language_confidence_threshold,
            translation_prefix=translation_prefix,
            translate_bot_messages=translate_bot_messages,
            translate_webhook_messages=translate_webhook_messages,
            reply_channels=reply_channels,
            sync_groups=sync_groups,
        )

    @staticmethod
    def _get_string_or_env(
        config: dict[str, object], key: str, env_var: str
    ) -> str:
        """Get a string from config or environment variable."""
        value = config.get(key, "")
        if isinstance(value, str) and value:
            return value
        env_value = os.environ.get(env_var, "")
        return env_value

    @staticmethod
    def _parse_reply_channels(config: dict[str, object]) -> tuple[ReplyChannelConfig, ...]:
        """Parse reply_channels from raw config."""
        raw_reply_channels = config.get("reply_channels", [])
        if not isinstance(raw_reply_channels, list):
            return ()

        reply_channels: list[ReplyChannelConfig] = []
        for item in raw_reply_channels:
            if not isinstance(item, dict):
                continue
            channel_id = item.get("channel_id")
            if not isinstance(channel_id, int):
                continue
            default_language = str(item.get("default_language", "en"))
            system_prompt = item.get("system_prompt")
            if not isinstance(system_prompt, str) or not system_prompt:
                system_prompt = None
            reply_channels.append(
                ReplyChannelConfig(
                    channel_id=channel_id,
                    default_language=default_language,
                    system_prompt=system_prompt,
                )
            )
        return tuple(reply_channels)

    @staticmethod
    def _parse_sync_groups(config: dict[str, object]) -> tuple[SyncGroupConfig, ...]:
        """Parse sync_groups from raw config."""
        raw_sync_groups = config.get("sync_groups", [])
        if not isinstance(raw_sync_groups, list):
            return ()

        sync_groups: list[SyncGroupConfig] = []
        for group in raw_sync_groups:
            if not isinstance(group, dict):
                continue
            name = str(group.get("name", "unnamed"))
            raw_channels = group.get("channels", [])
            if not isinstance(raw_channels, list):
                continue

            channels: list[SyncChannelConfig] = []
            for channel in raw_channels:
                if not isinstance(channel, dict):
                    continue
                channel_id = channel.get("channel_id")
                if not isinstance(channel_id, int):
                    continue
                language = str(channel.get("language", "en"))
                channels.append(
                    SyncChannelConfig(channel_id=channel_id, language=language)
                )

            system_prompt = group.get("system_prompt")
            if not isinstance(system_prompt, str) or not system_prompt:
                system_prompt = None

            if channels:
                sync_groups.append(
                    SyncGroupConfig(
                        name=name,
                        channels=tuple(channels),
                        system_prompt=system_prompt,
                    )
                )
        return tuple(sync_groups)

    def get_reply_channel_config(
        self, channel_id: int
    ) -> ReplyChannelConfig | None:
        """Get reply channel config by channel ID."""
        for reply_config in self.reply_channels:
            if reply_config.channel_id == channel_id:
                return reply_config
        return None

    def get_sync_channel_config(
        self, channel_id: int
    ) -> tuple[SyncGroupConfig, SyncChannelConfig] | None:
        """Get sync group and channel config by channel ID."""
        for group in self.sync_groups:
            for channel in group.channels:
                if channel.channel_id == channel_id:
                    return (group, channel)
        return None

    def get_system_prompt_for_channel(
        self, channel_id: int
    ) -> str:
        """Get the effective system prompt for a channel."""
        reply_config = self.get_reply_channel_config(channel_id)
        if reply_config is not None and reply_config.system_prompt is not None:
            return reply_config.system_prompt

        sync_config = self.get_sync_channel_config(channel_id)
        if sync_config is not None and sync_config[0].system_prompt is not None:
            return sync_config[0].system_prompt

        return self.system_prompt


CONFIG_FILE_NAME: Final = "config.toml"
CONFIG_FILE_PATHS: Final = [
    Path(CONFIG_FILE_NAME),
    Path.cwd() / CONFIG_FILE_NAME,
    Path.home() / ".config" / "discord-llm-translator" / CONFIG_FILE_NAME,
]


def load_config() -> BotConfig:
    """Load configuration from the first available config file."""
    for path in CONFIG_FILE_PATHS:
        if path.exists():
            return BotConfig.from_file(path)

    print(
        f"Error: No configuration file found. Please create a '{CONFIG_FILE_NAME}' file "
        "or copy 'config.sample.toml' and configure it.",
        file=sys.stderr,
    )
    sys.exit(1)
