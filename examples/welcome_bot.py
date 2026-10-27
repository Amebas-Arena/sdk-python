"""Um bot de sala completo: dá boas-vindas, responde !regras e rola um !dado com argumento, faixa e cooldown.

Rode contra a API de dev:
    eval "$(pnpm --silent --filter @amebas/bot-protocol dev-setup)"   # cria sala e chave, exporta AMEBAS_*
    uv run python examples/welcome_bot.py
"""

import asyncio
import os
import random

from amebas import RoomBot

bot = RoomBot(
    base_url=os.environ.get("AMEBAS_URL", "http://localhost:8092"),
    room_id=os.environ.get("AMEBAS_ROOM", ""),
    key=os.environ.get("AMEBAS_KEY", ""),
)


@bot.on_ready
async def pronto(ready):
    print(f'no ar na sala "{ready["room"]["name"]}"')


@bot.on_player_joined
async def boas_vindas(e):
    await bot.chat(f"Oi, {e['player']['nick']}! Digite !ajuda pra ver os comandos.")


# o caso simples: uma linha
@bot.command("regras")
async def regras(ctx):
    await ctx.reply("Sem xingar e joga limpo.")


# com argumento (lados vale 6 se a pessoa não disser), faixa, atalho e cooldown de 5 s por pessoa
@bot.command("dado", aliases=["d"], description="Rola um dado.", args={"lados": "int:2..100=6"}, cooldown=5)
async def dado(ctx):
    await ctx.reply(f"{ctx.player.nick} tirou {random.randint(1, ctx.args.lados)} (d{ctx.args.lados})")


# só a staff, e a define é um dict que dá pra reaproveitar
STAFF = dict(permission="staff", cooldown=30)


@bot.command("silencio", **STAFF, description="Pede silêncio.", args={"motivo": "rest?"})
async def silencio(ctx):
    extra = f" ({ctx.args.motivo})" if ctx.args.motivo else ""
    await ctx.reply(f"Silêncio, por favor!{extra}")


asyncio.run(bot.run())
