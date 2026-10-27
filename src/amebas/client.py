"""O cliente do bot de sala: abre o WebSocket /v1/rooms/{room_id}/bot, autentica pela primeira mensagem, entrega os
eventos tipados, manda comandos esperando o result de cada um e reconecta sozinho com espera crescente.

    bot = RoomBot(base_url="http://localhost:8092", room_id="...", key="amb_...")

    @bot.on_player_joined
    async def oi(e):
        await bot.chat(f"Oi, {e['player']['nick']}!")

    asyncio.run(bot.run())
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import random
import time
from typing import Any, Awaitable, Callable, Iterable, Mapping, Optional, Union
from urllib.parse import quote, urlsplit, urlunsplit

from ._events import EventDecorators
from .commands import Command, CommandError, CommandPlayer, Commands, Context, Person
from .types import ReadyMessage, RoomCommand

log = logging.getLogger("amebas")

BOT_PATH = "/v1/rooms/{room_id}/bot"
CLOSE_UNAUTHORIZED = 4001
CLOSE_INVALID_ROOM = 4004
# códigos do error que não melhoram tentando de novo (chave errada, sem escopo, sala de outra comunidade)
PERMANENT_ERRORS = {"unauthorized", "forbidden", "not_found"}

Handler = Callable[[Any], Union[None, Awaitable[None]]]


class RoomBotError(Exception):
    """O erro de um comando (o code e a mensagem do result) ou do canal."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def bot_url(base_url: str, room_id: str) -> str:
    """A URL do WebSocket a partir do endereço da API (http vira ws, https vira wss; o prefixo /api fica)."""
    parts = urlsplit(base_url)
    scheme = "wss" if parts.scheme in ("https", "wss") else "ws"
    path = parts.path.rstrip("/") + BOT_PATH.format(room_id=quote(room_id, safe=""))
    return urlunsplit((scheme, parts.netloc, path, "", ""))


class RoomBot(EventDecorators):
    """Um bot ligado a uma sala. Use `await bot.run()` (fica no ar até cair de vez) ou `async with bot:`."""

    def __init__(
        self,
        base_url: str,
        room_id: str,
        key: str,
        *,
        reconnect: bool = True,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        max_attempts: Optional[int] = None,
        command_timeout: float = 10.0,
        connect: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self.url = bot_url(base_url, room_id)
        self._key = key
        self._reconnect = reconnect
        self._initial_delay = initial_delay
        self._max_delay = max_delay
        self._max_attempts = max_attempts
        self._command_timeout = command_timeout
        self._connect = connect
        self._handlers: dict[str, list[Handler]] = {}
        self._pending: dict[str, asyncio.Future[None]] = {}
        self._next_ref = 0
        self._ws: Any = None
        self._ready = False
        self._tasks: set[asyncio.Task[Any]] = set()
        self._roster: dict[int, Person] = {}
        self.commands = Commands()
        self._watch_room()

    # --- eventos ---

    def on(self, event: str, handler: Optional[Handler] = None) -> Any:
        """Escuta um evento ('ready', 'chat.message', 'player.joined'...). Serve de decorador: @bot.on('chat.message').

        Os decoradores tipados (@bot.on_chat_message...) dão o tipo do evento pro editor.
        """

        def add(fn: Handler) -> Handler:
            self._handlers.setdefault(event, []).append(fn)
            return fn

        return add(handler) if handler is not None else add

    async def _emit(self, event: str, payload: Any) -> None:
        for fn in list(self._handlers.get(event, ())):
            try:
                result = fn(payload)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                log.exception("erro no handler de %s", event)

    # --- comandos do chat (!gols...) ---

    def command(
        self,
        name: str,
        handler: Optional[Callable[[Context], Any]] = None,
        *,
        aliases: Iterable[str] = (),
        description: str = "",
        hidden: bool = False,
        args: Optional[Mapping[str, Any]] = None,
        cooldown: Union[float, Mapping[str, Any], None] = None,
        permission: Optional[str] = None,
        messages: Optional[Mapping[str, str]] = None,
        parse: Optional[Callable[..., Any]] = None,
        define: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Registra um comando do chat. Serve de decorador; o caso simples cabe numa linha:

            @bot.command("regras")
            async def regras(ctx):
                await ctx.reply("Sem xingar.")

            @bot.command("gols", args={"n": "int:1..20"}, cooldown=10, permission="staff")
            async def gols(ctx):
                await ctx.reply(f"{ctx.args.n} gols")

        Arg errado, cooldown e permissão respondem sozinhos. A define é só keyword: guarde numa const e espalhe
        (`@bot.command("x", **STAFF)`), ou passe `define=STAFF`.
        """
        base = dict(define or {})
        base.update(
            {k: v for k, v in dict(
                aliases=tuple(aliases) or None, description=description or None, hidden=hidden or None, args=args,
                cooldown=cooldown, permission=permission, messages=messages, parse=parse,
            ).items() if v is not None}
        )

        def register(fn: Callable[[Context], Any]) -> Callable[[Context], Any]:
            self.commands.add(Command(
                name=name, handler=fn, aliases=tuple(base.get("aliases", ())), description=base.get("description", ""),
                hidden=base.get("hidden", False), args=base.get("args", {}), cooldown=base.get("cooldown"),
                permission=base.get("permission"), messages=base.get("messages"), parse=base.get("parse"),
            ))
            return fn

        return register(handler) if handler is not None else register

    def command_defaults(self, **defaults: Any) -> "RoomBot":
        """Os padrões de todos os comandos: bot.command_defaults(cooldown=3, permission="all")."""
        self.commands.defaults(**defaults)
        return self

    def _watch_room(self) -> None:
        @self.on("ready")
        def _(ready: ReadyMessage) -> None:
            self._roster = {
                p["id"]: Person(p["id"], p["nick"], p["accountId"]) for p in ((ready.get("live") or {}).get("players") or [])
            }

        @self.on("player.joined")
        def _(e: Any) -> None:
            p = e["player"]
            self._roster[p["id"]] = Person(p["id"], p["nick"], p["accountId"])

        @self.on("player.left")
        def _(e: Any) -> None:
            self._roster.pop(e["player"]["id"], None)

        @self.on("chat.message")
        async def _(e: Any) -> None:
            if not e.get("player"):
                return
            p = e["player"]
            player = CommandPlayer(p["id"], p["nick"], p["accountId"], e.get("role", "player"))
            # o handler roda numa tarefa: ele pode mandar comandos e esperar o result sem travar a leitura do socket
            self._spawn(self._run_command(e["text"], player))

    async def _run_command(self, text: str, player: CommandPlayer) -> None:
        async def say(t: str) -> None:
            try:
                await self.chat(t)
            except RoomBotError as err:
                log.warning("não consegui responder no chat: %s", err)

        try:
            await self.commands.dispatch(text, player, say, now=time.monotonic(), players=list(self._roster.values()))
        except Exception:
            log.exception("erro no comando %r", text.split(None, 1)[0] if text.split() else text)

    def _spawn(self, coro: Awaitable[Any]) -> None:
        task = asyncio.ensure_future(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    # --- comandos da sala ---

    @property
    def ready(self) -> bool:
        """Se a auth já foi aceita nesta conexão (comandos só saem com ela)."""
        return self._ready

    async def send(self, command: RoomCommand) -> None:
        """Manda um comando da sala e espera o result: volta com ok, ou levanta RoomBotError com o code do servidor."""
        if self._ws is None or not self._ready:
            raise RoomBotError("not_connected", "o bot não está conectado (espere o ready)")
        self._next_ref += 1
        ref = f"c{self._next_ref}"
        fut: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._pending[ref] = fut
        try:
            await self._ws.send(json.dumps({**command, "ref": ref}))
            await asyncio.wait_for(fut, self._command_timeout)
        except asyncio.TimeoutError:
            raise RoomBotError("timeout", f"o comando {command['type']} ficou sem resposta") from None
        finally:
            self._pending.pop(ref, None)

    async def chat(self, text: str) -> None:
        await self.send({"type": "chat", "text": text})

    async def kick(self, player_id: int) -> None:
        await self.send({"type": "kick", "playerId": player_id})

    async def ban(self, player_id: int, scope: str = "room") -> None:
        await self.send({"type": "ban", "playerId": player_id, "scope": scope})  # type: ignore[typeddict-item]

    async def mute(self, player_id: int, muted: bool = True) -> None:
        await self.send({"type": "mute", "playerId": player_id, "muted": muted})

    async def move(self, player_id: int, to: str) -> None:
        await self.send({"type": "move", "playerId": player_id, "to": to})  # type: ignore[typeddict-item]

    async def start(self) -> None:
        await self.send({"type": "start"})

    async def stop(self) -> None:
        await self.send({"type": "stop"})

    async def pause(self, paused: Optional[bool] = None) -> None:
        await self.send({"type": "pause"} if paused is None else {"type": "pause", "paused": paused})

    # --- conexão ---

    async def run(self) -> None:
        """Conecta e fica no ar até cancelar a tarefa ou parar de vez (auth recusada, sala inválida, tentativas
        esgotadas: levanta RoomBotError). Caiu por outro motivo, volta sozinho com espera crescente."""
        attempt = 0
        while True:
            got_ready, fatal = await self._session()
            if fatal is not None:
                raise fatal
            if got_ready:
                attempt = 0
            if not self._reconnect or (self._max_attempts is not None and attempt >= self._max_attempts):
                raise RoomBotError("disconnected", "a conexão caiu e o bot não vai tentar de novo")
            # espera crescente com sorteio (metade fixa, metade aleatória): muitos bots não voltam todos juntos
            base = min(self._max_delay, self._initial_delay * 2**attempt)
            attempt += 1
            await self._emit("reconnecting", {"attempt": attempt, "delay": base})
            await asyncio.sleep(base / 2 + random.random() * base / 2)

    async def __aenter__(self) -> "RoomBot":
        self._runner = asyncio.ensure_future(self.run())
        ready = asyncio.get_running_loop().create_future()
        self.on("ready", lambda r: ready.done() or ready.set_result(r))
        done, _ = await asyncio.wait({self._runner, ready}, return_when=asyncio.FIRST_COMPLETED)
        if self._runner in done:
            self._runner.result()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        self._runner.cancel()
        try:
            await self._runner
        except (asyncio.CancelledError, RoomBotError):
            pass

    async def _session(self) -> tuple[bool, Optional[RoomBotError]]:
        """Uma conexão do começo ao fim. Devolve se chegou a ter ready, e o erro quando não adianta repetir."""
        got_ready = False
        last_error: Optional[dict[str, Any]] = None
        try:
            if self._connect is not None:
                ws = await self._connect(self.url)
            else:
                import websockets

                ws = await websockets.connect(self.url, max_size=1 << 22)
        except (OSError, asyncio.TimeoutError, Exception) as err:  # noqa: BLE001
            log.warning("não conectou em %s: %s", self.url, err)
            return False, None
        self._ws = ws
        try:
            await ws.send(json.dumps({"type": "auth", "key": self._key}))
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                kind = msg.get("type")
                if kind == "ready":
                    got_ready, self._ready = True, True
                elif kind == "result":
                    fut = self._pending.get(msg.get("ref", ""))
                    if fut and not fut.done():
                        if msg.get("ok"):
                            fut.set_result(None)
                        else:
                            fut.set_exception(RoomBotError(msg.get("code", "error"), msg.get("message", "comando recusado")))
                    continue
                elif kind == "error":
                    last_error = msg
                await self._emit("message", msg)
                await self._emit(kind, msg)
                if kind not in ("ready", "error", "result"):
                    await self._emit("event", msg)
        except Exception as err:  # noqa: BLE001 — a conexão caiu; o motivo vai pro log e a decisão fica abaixo
            if not _is_closed(err):
                log.warning("conexão caiu: %s", err)
        finally:
            self._ready = False
            self._ws = None
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(RoomBotError("disconnected", "a conexão caiu antes do result"))
            code = _close_code(ws)
            try:
                await ws.close()
            except Exception:  # noqa: BLE001
                pass
        if code == CLOSE_INVALID_ROOM:
            return got_ready, RoomBotError("invalid", "id de sala inválido")
        if code == CLOSE_UNAUTHORIZED and last_error and last_error.get("code") in PERMANENT_ERRORS:
            return got_ready, RoomBotError(last_error["code"], last_error.get("message", ""))
        return got_ready, None


def _close_code(ws: Any) -> Optional[int]:
    rcvd = getattr(ws, "close_rcvd", None)
    if rcvd is not None:
        return rcvd.code
    return getattr(ws, "close_code", None)


def _is_closed(err: Exception) -> bool:
    return type(err).__name__.startswith("ConnectionClosed")
