"""SDK oficial do bot de sala do Amebas Arena.

    from amebas import RoomBot

    bot = RoomBot(base_url="http://localhost:8092", room_id="...", key="amb_...")

    @bot.command("regras")
    async def regras(ctx):
        await ctx.reply("Sem xingar.")

    asyncio.run(bot.run())
"""

from .client import RoomBot, RoomBotError, bot_url
from .commands import (
    Args,
    Command,
    CommandError,
    CommandPlayer,
    Commands,
    Context,
    DefinitionError,
    Person,
    format_wait,
)
from .types import *  # noqa: F401,F403 — os TypedDicts gerados do protocolo

__all__ = [
    "Args",
    "Command",
    "CommandError",
    "CommandPlayer",
    "Commands",
    "Context",
    "DefinitionError",
    "Person",
    "RoomBot",
    "RoomBotError",
    "bot_url",
    "format_wait",
]
