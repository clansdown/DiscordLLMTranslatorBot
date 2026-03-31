"""Entry point for the Discord LLM Translator Bot."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from discord_llm_translator.bot import DiscordTranslatorBot
from discord_llm_translator.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for running the bot."""
    logger.info("Starting Discord LLM Translator Bot...")

    try:
        config = load_config()
    except SystemExit:
        return

    bot = DiscordTranslatorBot(config)
    shutdown_event = asyncio.Event()

    def handle_signal() -> None:
        logger.info("Received shutdown signal")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except (NotImplementedError, ValueError):
            pass

    bot_task = asyncio.create_task(bot.start())
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    try:
        done, pending = await asyncio.wait(
            [bot_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in done:
            exc = task.exception()
            if exc is not None:
                logger.exception(f"Task failed: {exc}")

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    finally:
        await bot.shutdown()
        logger.info("Bot shutdown complete")


def main_wrapper() -> None:
    """Wrapper for running main with proper exception handling."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main_wrapper()
