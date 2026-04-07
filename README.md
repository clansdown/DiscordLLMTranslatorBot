# Discord LLM Translator Bot

A Discord bot that provides automatic translation using LLMs via OpenRouter.ai with Zero Data Retention (ZDR) policies.

## Features

- **Reply Mode**: Monitor channels for messages not in the default language and auto-reply with translations
- **Sync Mode**: Synchronize messages across channels in different languages
- **Configurable System Prompts**: Customize translation behavior per channel or globally
- **Language Detection**: Automatic detection using langdetect library
- **Rate Limiting**: Per-user rate limiting to prevent spam
- **ZDR Compliance**: Uses OpenRouter models with Zero Data Retention policies

## Requirements

- Python 3.11+
- Discord bot token
- OpenRouter API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DiscordLLMTranslatorBot.git
cd DiscordLLMTranslatorBot
```

2. Run the install script (installs uv and dependencies):
```bash
./install.sh
```

3. Edit `config.toml` with your Discord token and OpenRouter API key.

## Configuration

Edit `config.toml` with your settings:

```toml
discord_token = "YOUR_DISCORD_TOKEN"
openrouter_api_key = "YOUR_OPENROUTER_API_KEY"
model = "google/gemini-2.5-flash"

# Reply mode: auto-translate messages not in the target language
[[reply_channels]]
channel_id = 123456789012345678
default_language = "en"

# Sync mode: synchronize messages across channels
[[sync_groups]]
name = "general"
channels = [
    { channel_id = 111111111111111111, language = "en" },
    { channel_id = 222222222222222222, language = "es" },
]
```

See `config.sample.toml` for all available options with documentation.

## Running the Bot

```bash
./run.sh
```

Or manually:
```bash
source .venv/bin/activate
python -m discord_llm_translator
```

## Environment Variables

The following environment variables can be used instead of config values:

- `DISCORD_TOKEN` - Discord bot token
- `OPENROUTER_API_KEY` - OpenRouter API key

## Development

After installation, run linting:
```bash
ruff check src/
```

Run type checking:
```bash
mypy src/
```

## License

This project is licensed under the GNU AGPL-3.0 license. See [LICENSE](LICENSE) for details.
