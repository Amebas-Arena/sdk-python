"""O cliente contra um servidor WebSocket local (o da biblioteca websockets): auth pela primeira mensagem, ready,
eventos tipados, comandos com ref e result, comandos do chat respondendo pelo chat e a reconexão."""

import asyncio
import json

import pytest
from websockets.asyncio.server import serve

from amebas import RoomBot, RoomBotError, bot_url

READY = {
    "type": "ready",
    "room": {"id": "r1"},
    "live": {"code": "ABCD", "address": None, "phase": "stopped", "score": {"a": 0, "b": 0}, "mode": "football", "map": "m", "players": []},
}


class FakeApi:
    """Servidor do bot de sala de mentira: guarda o que o bot manda e deixa o teste responder."""

    def __init__(self, on_auth=None):
        self.conns = []
        self.got: asyncio.Queue = asyncio.Queue()
        self.on_auth = on_auth or (lambda ws, msg: ws.send(json.dumps(READY)))

    async def handler(self, ws):
        self.conns.append(ws)
        async for raw in ws:
            msg = json.loads(raw)
            if msg["type"] == "auth":
                self.auth = msg
                await self.on_auth(ws, msg)
            else:
                await self.got.put(msg)

    async def next(self):
        return await asyncio.wait_for(self.got.get(), 2)


@pytest.fixture
async def api():
    fake = FakeApi()
    async with serve(fake.handler, "127.0.0.1", 0) as server:
        fake.url = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        yield fake


def test_bot_url():
    assert bot_url("http://localhost:8092", "r1") == "ws://localhost:8092/v1/rooms/r1/bot"
    assert bot_url("https://amebas.site/api/", "a b") == "wss://amebas.site/api/v1/rooms/a%20b/bot"


async def test_auth_ready_events_and_chat(api):
    bot = RoomBot(api.url, "r1", "amb_x", reconnect=False)
    joined, ready = asyncio.Queue(), asyncio.Queue()
    bot.on("ready", ready.put_nowait)

    @bot.on_player_joined
    async def _(e):
        await joined.put(e["player"]["nick"])

    task = asyncio.create_task(bot.run())
    assert (await asyncio.wait_for(ready.get(), 2))["live"]["code"] == "ABCD"
    assert api.auth == {"type": "auth", "key": "amb_x"}

    chat = asyncio.create_task(bot.chat("oi"))
    m = await api.next()
    assert m["type"] == "chat" and m["text"] == "oi" and m["ref"]
    await api.conns[0].send(json.dumps({"type": "result", "ref": m["ref"], "ok": True}))
    await chat

    kick = asyncio.create_task(bot.kick(9))
    m = await api.next()
    await api.conns[0].send(json.dumps({"type": "result", "ref": m["ref"], "ok": False, "code": "not_found", "message": "sem ele"}))
    with pytest.raises(RoomBotError) as err:
        await kick
    assert err.value.code == "not_found" and err.value.message == "sem ele"

    await api.conns[0].send(json.dumps({"type": "player.joined", "roomId": "r1", "at": 1, "players": 1, "player": {"id": 2, "nick": "Ana", "accountId": None}}))
    assert await asyncio.wait_for(joined.get(), 2) == "Ana"
    task.cancel()


async def test_command_before_ready():
    bot = RoomBot("http://localhost:1", "r1", "k")
    with pytest.raises(RoomBotError, match="espere o ready"):
        await bot.chat("oi")


async def test_chat_commands_reply_in_chat(api):
    bot = RoomBot(api.url, "r1", "amb_x", reconnect=False)
    seen = []

    @bot.command("gols", args={"n": "int:1..20"}, cooldown=10, permission="staff")
    async def gols(ctx):
        seen.append(ctx.args.n + 1)  # ctx.args.n e ctx.args["n"] são o mesmo

    ready = asyncio.Queue()
    bot.on("ready", ready.put_nowait)
    task = asyncio.create_task(bot.run())
    await ready.get()

    async def say(role, text):
        await api.conns[0].send(json.dumps({"type": "chat.message", "roomId": "r1", "at": 1, "text": text, "role": role, "player": {"id": 3, "nick": "Bia", "accountId": "acc-bia"}}))

    async def reply():
        m = await api.next()
        await api.conns[0].send(json.dumps({"type": "result", "ref": m["ref"], "ok": True}))
        return m["text"]

    await say("player", "!gols 5")
    assert await reply() == "Só a staff pode usar !gols."
    await say("staff", "!gols 99")
    assert await reply() == "Valor inválido pra n: um número inteiro de 1 a 20. Uso: !gols <n>"
    await say("staff", "!gols 4")
    for _ in range(100):
        if seen:
            break
        await asyncio.sleep(0.01)
    assert seen == [5]
    task.cancel()


async def test_reconnects_and_resends_auth(api):
    bot = RoomBot(api.url, "r1", "amb_x", initial_delay=0.001, max_delay=0.002)
    readies = asyncio.Queue()
    bot.on("ready", readies.put_nowait)
    task = asyncio.create_task(bot.run())
    await readies.get()
    await api.conns[0].close(1001)
    await asyncio.wait_for(readies.get(), 2)
    assert len(api.conns) == 2
    task.cancel()


async def test_refused_auth_does_not_reconnect():
    async def refuse(ws, msg):
        await ws.send(json.dumps({"type": "error", "code": "unauthorized", "message": "chave inválida"}))
        await ws.close(4001, "auth")

    fake = FakeApi(refuse)
    async with serve(fake.handler, "127.0.0.1", 0) as server:
        bot = RoomBot(f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}", "r1", "amb_errada", initial_delay=0.001)
        with pytest.raises(RoomBotError) as err:
            await asyncio.wait_for(bot.run(), 3)
        assert err.value.code == "unauthorized" and err.value.message == "chave inválida"
        assert len(fake.conns) == 1
