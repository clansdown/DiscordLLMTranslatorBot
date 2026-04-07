#!/usr/bin/env bash
set -e

echo "Installing Discord LLM Translator Bot..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the new path
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create virtual environment
echo "Creating virtual environment..."
uv venv

# Install dependencies
echo "Installing dependencies..."
uv pip install -e . --extra dev

# Copy config if needed
if [ ! -f config.toml ]; then
    echo "Creating config.toml from sample..."
    cp config.sample.toml config.toml
    echo ""
    echo "Please edit config.toml with your Discord token and OpenRouter API key"
fi

echo ""
echo "Installation complete!"
echo "  - Run with: ./run.sh"
echo "  - Or: source .venv/bin/activate && python -m discord_llm_translator"
