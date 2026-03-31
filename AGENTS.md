# Agent Instructions for Discord LLM Translator Bot

This document provides instructions for AI agents working on this codebase.

## Project Overview

Discord LLM Translator Bot is a Python Discord bot that provides automatic translation using LLMs via OpenRouter.ai. It supports two modes:

1. **Reply Mode**: Monitors channels for messages not in the default language, replies with translations
2. **Sync Mode**: Synchronizes messages across channels in different languages

## Project Structure

```
DiscordLLMTranslatorBot/
├── config.toml              # Runtime configuration (gitignored)
├── config.sample.toml       # Sample configuration with comments
├── pyproject.toml           # Project metadata and dependencies
├── src/discord_llm_translator/
│   ├── __init__.py          # Package init
│   ├── __main__.py          # CLI entry point
│   ├── bot.py               # Main bot class
│   ├── config.py            # Configuration loading and dataclasses
│   ├── constants.py         # Default values and constants
│   ├── cogs/
│   │   ├── __init__.py
│   │   └── translation.py   # Translation event handlers
│   ├── models/
│   │   ├── __init__.py
│   │   └── translation.py   # Translation data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openrouter_client.py   # OpenRouter API client
│   │   └── language_detector.py  # Language detection service
│   └── utils/
│       ├── __init__.py
│       └── formatting.py    # Message formatting utilities
└── README.md
```

## Key Components

### Configuration (`config.py`)

- Uses TOML format for configuration
- Configuration can be loaded from multiple paths (see `CONFIG_FILE_PATHS`)
- Environment variables supported: `DISCORD_TOKEN`, `OPENROUTER_API_KEY`
- Key dataclasses:
  - `BotConfig`: Main configuration container
  - `ReplyChannelConfig`: Reply mode channel settings
  - `SyncGroupConfig`: Sync group with channels
  - `SyncChannelConfig`: Individual channel in a sync group

### Services

**OpenRouterClient** (`services/openrouter_client.py`):
- Async HTTP client for OpenRouter API
- ZDR policy headers for data privacy
- Retry logic with exponential backoff
- System prompt template interpolation with `{source_language}` and `{target_language}`

**LanguageDetector** (`services/language_detector.py`):
- Wrapper around `langdetect` library
- Confidence threshold support
- Quick detection with LRU caching via `detect_language_quick()`

### Translation Handler (`cogs/translation.py`)

- `TranslationHandler` class handles all translation logic
- `RateLimiter` for per-user rate limiting
- Message deduplication for sync mode
- System prompt resolution hierarchy:
  1. Channel-specific prompt
  2. Sync group prompt
  3. Global prompt
  4. Built-in default
- Listeners registered in `bot.py` via `client.add_listener()`

### Bot (`bot.py`)

- Initializes services and handler
- Registers Discord event listeners
- Handles graceful shutdown

## Development Commands

### Install dependencies

```bash
pip install -e ".[dev]"
```

### Run the bot

```bash
python -m discord_llm_translator
```

### Run linting (ruff)

```bash
ruff check src/
```

### Run type checking (mypy)

```bash
mypy src/
```

## Adding New Features

### Adding a new configuration option

1. Add the field to `config.sample.toml` with documentation
2. Add parsing logic in `BotConfig.from_file()` in `config.py`
3. Add the field to `BotConfig` dataclass
4. Update `config.py` imports from `constants.py` if adding defaults

### Adding a new service

1. Create the service module in `services/`
2. Add to `services/__init__.py` exports
3. Instantiate in `bot.py` `DiscordTranslatorBot.setup()`
4. Pass to relevant handlers

### Adding a new Discord event handler

1. Add the method to `TranslationHandler` in `cogs/translation.py`
2. Register in `bot.py` `DiscordTranslatorBot.setup()` using `self._client.add_listener()`

## Testing

When modifying this codebase:
1. Ensure `ruff check` passes with no errors
2. Ensure `mypy` passes with no errors (or update types if needed)
3. Test the specific feature being modified
4. Verify config parsing with new options

## Important Notes

- **Static typing**: All code should use type hints where possible
- **No mutable defaults**: Use `tuple` instead of `list` for frozen dataclass fields
- **Async handling**: Use `asyncio.Lock` for shared state modifications
- **Error handling**: Catch specific exceptions, log errors, don't crash the bot
- **Config validation**: Validate required fields in `BotConfig.from_file()`
