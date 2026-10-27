"""O sistema de comandos do chat ("!gols 5"): a define de cada comando (args, cooldown, permissão), o parser padrão,
as respostas prontas (uso errado, cooldown, sem permissão) e o !ajuda gerado sozinho.

É o mesmo contrato do script do painel e dos SDKs de TypeScript e Go; os casos de protocol/commands.conformance.json
valem pros quatro. A classe Commands funciona sozinha (sem o bot), com outro transporte.
"""

from __future__ import annotations

import inspect
import math
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Iterable, Literal, Mapping, Optional, Union

Role = Literal["player", "staff", "owner"]
Permission = Literal["all", "staff", "owner"]

NAME = re.compile(r"^[a-z0-9_-]{1,24}$")
HELP_NAMES = ("ajuda", "help", "comandos")
TYPES = ("int", "number", "text", "rest", "bool", "player", "team")
TRUE_WORDS = ("sim", "s", "yes", "y", "true", "1", "on", "liga")
FALSE_WORDS = ("não", "nao", "n", "no", "false", "0", "off", "desliga")
MAX_CHAT = 200
DEFAULT_MESSAGES = {
    "usage": "{reason}. Uso: {usage}",
    "cooldown": "Espere {left} pra usar {command} de novo.",
    "permission": "Só {who} pode usar {command}.",
}
_RANK = {"player": 0, "staff": 1, "owner": 2, "all": 0}


class CommandError(Exception):
    """O motivo de um argumento ruim: o parse próprio (ou o handler) levanta isto e a pessoa recebe a resposta de uso."""


class DefinitionError(ValueError):
    """Erro de quem escreve o bot (tipo que não existe, faixa torta): diz o que está errado e o jeito certo."""


class Args(dict):
    """Os argumentos já convertidos: ctx.args["n"] ou ctx.args.n."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"esse comando não tem o argumento {name!r} (tem: {', '.join(self) or 'nenhum'})") from None


@dataclass(frozen=True)
class Person:
    """Quem está na sala, como o argumento `player` devolve."""

    id: int
    nick: str
    account_id: Optional[str] = None


@dataclass(frozen=True)
class CommandPlayer(Person):
    """Quem mandou o comando: a Person e o papel na sala (dono, staff ou jogador)."""

    role: Role = "player"


@dataclass
class Context:
    """O que o handler recebe."""

    player: CommandPlayer
    args: Args
    command: str
    alias: str
    words: list[str]
    rest: str
    _reply: Callable[[str], Any] = field(repr=False, default=lambda text: None)

    def reply(self, text: str) -> Any:
        """Responde pra quem mandou (no bot, é uma linha no chat da sala). No bot, use `await ctx.reply(...)`."""
        return self._reply(text)


@dataclass
class Command:
    """A define de um comando, já com os padrões resolvidos na hora de usar."""

    name: str
    handler: Callable[[Context], Any]
    aliases: tuple[str, ...] = ()
    description: str = ""
    hidden: bool = False
    args: Mapping[str, Any] = field(default_factory=dict)
    cooldown: Union[float, Mapping[str, Any], None] = None
    permission: Optional[Permission] = None
    messages: Optional[Mapping[str, str]] = None
    parse: Optional[Callable[..., Any]] = None


@dataclass
class _Arg:
    name: str
    type: str
    min: Optional[float] = None
    max: Optional[float] = None
    choices: tuple[str, ...] = ()
    optional: bool = False
    has_default: bool = False
    default: Any = None


@dataclass
class _Registered:
    name: str
    command: Command
    args: list[_Arg]
    players: dict[str, float] = field(default_factory=dict)
    room: float = 0.0


@dataclass
class Match:
    """O que fazer com a mensagem: rodar um comando (e depois dizer se contou) ou responder."""

    replies: list[str] = field(default_factory=list)
    command: Optional[str] = None
    alias: str = ""
    args: Args = field(default_factory=Args)
    words: list[str] = field(default_factory=list)
    rest: str = ""
    _finish: Callable[[bool], None] = field(repr=False, default=lambda counted: None)
    _usage: Callable[[str], str] = field(repr=False, default=lambda reason: reason)

    @property
    def is_run(self) -> bool:
        return self.command is not None

    def finish(self, counted: bool) -> None:
        """Fecha o uso: counted=False devolve o cooldown."""
        self._finish(counted)

    def usage(self, reason: str) -> str:
        """A resposta de uso com o motivo (o CommandError que o handler levantou)."""
        return self._usage(reason)


def format_wait(seconds: float) -> str:
    """9s, 1min, 1min 5s (sempre arredondando pra cima: "espere 1s" e não "0s")."""
    s = math.ceil(seconds)
    if s < 60:
        return f"{s}s"
    m, rest = divmod(s, 60)
    return f"{m}min {rest}s" if rest else f"{m}min"


def _show(n: float) -> str:
    text = str(int(n)) if float(n).is_integer() else str(n)
    return text.replace(".", ",")


def _fill(template: str, values: Mapping[str, str]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), template)


def _def_error(command: str, problem: str) -> DefinitionError:
    return DefinitionError(f"comando !{command}: {problem}")


_RANGE = re.compile(r"^(-?\d+(?:\.\d+)?)?\.\.(-?\d+(?:\.\d+)?)?$")
_INT = re.compile(r"^[+-]?\d{1,15}$")
_NUMBER = re.compile(r"^[+-]?\d{1,15}([.,]\d{1,15})?$")


def parse_arg_spec(command: str, name: str, spec: Union[str, Mapping[str, Any]]) -> _Arg:
    """A forma curta ('int:1..20?') ou o dict ({'type': 'int', 'min': 1, 'default': 5}) na forma completa."""
    if not isinstance(spec, str):
        kind = spec.get("type")
        if kind != "choice" and kind not in TYPES:
            raise _def_error(command, f"o tipo de {name!r} ({kind}) não existe; use {', '.join(TYPES)} ou choice")
        if kind == "choice" and not spec.get("choices"):
            raise _def_error(command, f"{name!r} é choice e precisa de choices: ['a', 'b']")
        has_default = spec.get("default") is not None
        return _Arg(
            name, kind, spec.get("min"), spec.get("max"), tuple(spec.get("choices", ())),
            has_default or bool(spec.get("optional")), has_default, spec.get("default"),
        )
    base = spec.strip()
    raw_default: Optional[str] = None
    if "=" in base:
        base, raw_default = base.split("=", 1)
    optional = raw_default is not None
    if base.endswith("?"):
        optional, base = True, base[:-1]
    arg = _Arg(name, "text", optional=optional)
    if "|" in base:
        arg.type = "choice"
        arg.choices = tuple(c.strip() for c in base.split("|"))
        if not all(arg.choices):
            raise _def_error(command, f"{name!r}: opção vazia em {spec!r}")
    else:
        kind, _, rng = base.partition(":")
        if kind not in TYPES:
            raise _def_error(command, f"o tipo de {name!r} ({spec!r}) não existe; use {', '.join(TYPES)}, ou opções como 'azul|vermelho'")
        arg.type = kind
        if ":" in base:
            m = _RANGE.match(rng)
            if not m or (m.group(1) is None and m.group(2) is None) or kind not in ("int", "number", "text"):
                raise _def_error(command, f"faixa inválida em {name!r} ({spec!r}); o jeito é 'int:1..20', 'int:1..' ou 'int:..20'")
            arg.min = None if m.group(1) is None else float(m.group(1))
            arg.max = None if m.group(2) is None else float(m.group(2))
    if raw_default is not None:
        if arg.type in ("player", "rest"):
            raise _def_error(command, f"{name!r} ({arg.type}) não aceita valor padrão; use '?' pra deixar opcional")
        value, bad = _convert(arg, raw_default)
        if bad:
            raise _def_error(command, f"o padrão de {name!r} ({raw_default!r}) não vale: {bad}")
        arg.has_default, arg.default = True, value
    return arg


def _range_text(a: _Arg) -> str:
    if a.min is not None and a.max is not None:
        return f" de {_show(a.min)} a {_show(a.max)}"
    if a.min is not None:
        return f" a partir de {_show(a.min)}"
    if a.max is not None:
        return f" até {_show(a.max)}"
    return ""


def _expect(a: _Arg) -> str:
    if a.type == "int":
        return f"um número inteiro{_range_text(a)}"
    if a.type == "number":
        return f"um número{_range_text(a)}"
    if a.type == "text":
        return "um texto" if a.min is None and a.max is None else f"um texto{_range_text(a)} letras"
    if a.type == "bool":
        return "sim ou não"
    if a.type == "team":
        return "a ou b"
    return f"uma destas opções: {', '.join(a.choices)}"


def _in_range(a: _Arg, n: float) -> bool:
    return (a.min is None or n >= a.min) and (a.max is None or n <= a.max)


def _convert(a: _Arg, word: str) -> tuple[Any, Optional[str]]:
    bad = f"Valor inválido pra {a.name}: {_expect(a)}"
    lower = word.lower()
    if a.type == "int":
        if not _INT.match(word):
            return None, bad
        n = int(word)
        return (n, None) if _in_range(a, n) else (None, bad)
    if a.type == "number":
        if not _NUMBER.match(word):
            return None, bad
        n = float(word.replace(",", "."))
        return (n, None) if _in_range(a, n) else (None, bad)
    if a.type == "text":
        return (word, None) if _in_range(a, len(word)) else (None, bad)
    if a.type == "bool":
        if lower in TRUE_WORDS:
            return True, None
        if lower in FALSE_WORDS:
            return False, None
        return None, bad
    if a.type == "team":
        return (lower, None) if lower in ("a", "b") else (None, bad)
    if a.type == "choice":
        for choice in a.choices:
            if choice.lower() == lower:
                return choice, None
        return None, bad
    return word, None


def _find_player(word: str, players: Iterable[Person]) -> tuple[Optional[Person], Optional[str]]:
    people = list(players)
    if re.fullmatch(r"#\d+", word):
        pid = int(word[1:])
        for p in people:
            if p.id == pid:
                return p, None
        return None, f"Ninguém na sala com o id {word}"
    typed = word[1:] if word.startswith("@") else word
    lower = typed.lower()
    for p in people:
        if p.nick.lower() == lower:
            return p, None
    starts = [p for p in people if p.nick.lower().startswith(lower)]
    if len(starts) == 1:
        return starts[0], None
    if len(starts) > 1:
        names = ", ".join(p.nick for p in starts[:5])
        return None, f'Mais de um jogador combina com "{typed}": {names}{"..." if len(starts) > 5 else ""}'
    return None, f'Ninguém na sala com o nick "{typed}"'


def _usage_of(prefix: str, r: _Registered) -> str:
    parts = [f"{prefix}{r.name}"]
    for a in r.args:
        label = a.name + ("..." if a.type == "rest" else "")
        parts.append(f"[{label}]" if a.optional else f"<{label}>")
    return " ".join(parts)


def _cooldown_of(value: Union[float, int, Mapping[str, Any], None]) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {k: v for k, v in value.items() if k in ("player", "room", "exempt_staff", "exemptStaff")}
    return {"player": value}


class Commands:
    """Os comandos de uma sala (ou de um bot): registra, decide o que cada mensagem é e guarda os cooldowns."""

    def __init__(self) -> None:
        self._base: dict[str, Any] = {"cooldown": {}, "messages": {}}
        self._list: list[_Registered] = []
        self._by_name: dict[str, _Registered] = {}

    def defaults(
        self,
        *,
        cooldown: Union[float, Mapping[str, Any], None] = None,
        permission: Optional[Permission] = None,
        messages: Optional[Mapping[str, str]] = None,
        prefix: Optional[str] = None,
        help: Optional[bool] = None,
    ) -> "Commands":
        """Os padrões de todos os comandos (a define de cada um sobrescreve campo a campo)."""
        if prefix is not None:
            if not re.fullmatch(r"\S{1,3}", prefix):
                raise ValueError(f"defaults: prefix tem que ter de 1 a 3 caracteres sem espaço (veio {prefix!r})")
            self._base["prefix"] = prefix
        if cooldown is not None:
            self._base["cooldown"] = {**self._base["cooldown"], **_cooldown_of(cooldown)}
        if permission is not None:
            self._base["permission"] = permission
        if messages:
            self._base["messages"] = {**self._base["messages"], **messages}
        if help is not None:
            self._base["help"] = help
        return self

    def add(self, command: Command) -> "Commands":
        """Registra um comando; o mesmo nome de novo substitui o anterior."""
        n = command.name.strip().lower().removeprefix("!")
        if not NAME.match(n):
            raise ValueError(f"nome de comando inválido: {command.name!r} (letras minúsculas, números, _ ou -, até 24)")
        if not callable(command.handler):
            raise _def_error(n, "a função do comando está faltando: @bot.command('nome') em cima de uma função")
        args = [parse_arg_spec(n, k, v) for k, v in command.args.items()]
        for i, a in enumerate(args):
            if a.type == "rest" and i != len(args) - 1:
                raise _def_error(n, f"{a.name!r} é rest (o resto da linha) e tem que ser o último argumento")
        aliases = tuple(a.strip().lower().removeprefix("!") for a in command.aliases)
        for a in aliases:
            if not NAME.match(a):
                raise _def_error(n, f"atalho inválido: {a!r} (letras minúsculas, números, _ ou -, até 24)")
        old = self._by_name.get(n)
        if old:
            self._list.remove(old)
            for k in [k for k, v in self._by_name.items() if v is old]:
                del self._by_name[k]
        command.name, command.aliases = n, aliases
        reg = _Registered(n, command, args)
        self._list.append(reg)
        for key in (n, *aliases):
            self._by_name[key] = reg
        return self

    def names(self) -> list[str]:
        return [r.name for r in self._list]

    def triggers(self) -> list[str]:
        """Tudo que dispara um comando daqui, com o prefixo (nomes, atalhos e o !ajuda embutido)."""
        r = self._resolve(None)
        out = list(self._by_name)
        if r["help"]:
            out += [h for h in HELP_NAMES if h not in self._by_name]
        return sorted(r["prefix"] + n for n in out)

    def _resolve(self, reg: Optional[_Registered]) -> dict[str, Any]:
        c = reg.command if reg else None
        cooldown = {"player": 0, "room": 0, "exempt_staff": True, **self._base["cooldown"], **_cooldown_of(c.cooldown if c else None)}
        if "exemptStaff" in cooldown:
            cooldown["exempt_staff"] = cooldown.pop("exemptStaff")
        return {
            "prefix": self._base.get("prefix", "!"),
            "help": self._base.get("help", True),
            "cooldown": cooldown,
            "permission": (c.permission if c and c.permission else None) or self._base.get("permission", "all"),
            "messages": {**DEFAULT_MESSAGES, **self._base["messages"], **((c.messages or {}) if c else {})},
        }

    def match(self, text: str, player: CommandPlayer, now: float, players: Iterable[Person] = ()) -> Optional[Match]:
        """Decide o que a mensagem é: None = não é comando daqui. `now` em segundos (qualquer relógio crescente)."""
        prefix = self._resolve(None)["prefix"]
        text = text.strip()
        if not text.startswith(prefix):
            return None
        after = text[len(prefix):]
        words = list(re.finditer(r"\S+", after))
        if not words or words[0].start() != 0:
            return None
        alias = words[0].group().lower()
        rest = after[words[1].start():].strip() if len(words) > 1 else ""
        reg = self._by_name.get(alias)
        if reg is None:
            return self._help_for(alias, player, words[1:])
        res = self._resolve(reg)
        values = {"command": f"{res['prefix']}{reg.name}", "nick": player.nick, "usage": _usage_of(res["prefix"], reg)}

        def reply(template: str, **extra: str) -> Match:
            return Match(replies=[_fill(template, {**values, **extra})])

        if _RANK[player.role] < _RANK[res["permission"]]:
            return reply(res["messages"]["permission"], who="o dono da sala" if res["permission"] == "owner" else "a staff")

        plain = [w.group() for w in words[1:]]
        try:
            if reg.command.parse:
                args = Args(reg.command.parse(rest=rest, words=plain, player=player, players=list(players)))
            else:
                args = self._parse_args(reg, words[1:], after, list(players))
        except CommandError as err:
            return reply(res["messages"]["usage"], reason=str(err))

        cd = res["cooldown"]
        exempt = _RANK[player.role] >= 1 and cd["exempt_staff"]
        key = f"acc:{player.account_id}" if player.account_id else f"nick:{player.nick.lower()}"
        if not exempt:
            for until in (reg.players.get(key, 0.0), reg.room):
                if until - now > 0:
                    return reply(res["messages"]["cooldown"], left=format_wait(until - now))
        before = (reg.players.get(key), reg.room)
        if not exempt:
            if cd["player"] > 0:
                reg.players[key] = now + cd["player"]
            if cd["room"] > 0:
                reg.room = now + cd["room"]

        def finish(counted: bool) -> None:
            if counted or exempt:
                return
            if before[0] is None:
                reg.players.pop(key, None)
            else:
                reg.players[key] = before[0]
            reg.room = before[1]

        return Match(
            command=reg.name, alias=alias, args=args, words=plain, rest=rest, _finish=finish,
            _usage=lambda reason: _fill(res["messages"]["usage"], {**values, "reason": reason}),
        )

    def _parse_args(self, reg: _Registered, words: list[re.Match[str]], after: str, players: list[Person]) -> Args:
        out = Args()
        i = 0
        for a in reg.args:
            if a.type == "rest":
                value = after[words[i].start():].strip() if i < len(words) else ""
                i = len(words)
                if value:
                    out[a.name] = value
                elif a.optional:
                    out[a.name] = None
                else:
                    raise CommandError(f"Faltou {a.name}")
                continue
            if i >= len(words):
                if not a.optional:
                    raise CommandError(f"Faltou {a.name}")
                out[a.name] = a.default if a.has_default else None
                continue
            word = words[i].group()
            i += 1
            if a.type == "player":
                person, bad = _find_player(word, players)
                if bad:
                    raise CommandError(bad)
                out[a.name] = person
                continue
            value, bad = _convert(a, word)
            if bad:
                raise CommandError(bad)
            out[a.name] = value
        return out

    def _help_for(self, alias: str, player: CommandPlayer, words: list[re.Match[str]]) -> Optional[Match]:
        r = self._resolve(None)
        if not r["help"] or alias not in HELP_NAMES:
            return None
        p = r["prefix"]

        def can_use(x: _Registered) -> bool:
            return not x.command.hidden and _RANK[player.role] >= _RANK[self._resolve(x)["permission"]]

        if words:
            asked = words[0].group()
            asked = (asked[len(p):] if asked.startswith(p) else asked).lower().removeprefix("!")
            x = self._by_name.get(asked)
            if x is None or not can_use(x):
                return Match(replies=[f"Não tem o comando {p}{asked}. Use {p}ajuda pra ver a lista."])
            line = _usage_of(p, x)
            if x.command.description:
                line += f": {x.command.description}"
            if x.command.aliases:
                line += " Atalhos: " + ", ".join(p + a for a in x.command.aliases) + "."
            cd = self._resolve(x)["cooldown"]["player"]
            if cd > 0:
                line += f" Espera: {format_wait(cd)}."
            return Match(replies=[line])
        names = [p + x.name for x in self._list if can_use(x)]
        return Match(replies=_chunk_list(names, f" Pra ver como usar um: {p}ajuda <comando>"))

    async def dispatch(
        self,
        text: str,
        player: CommandPlayer,
        reply: Callable[[str], Union[None, Awaitable[None]]],
        *,
        now: float,
        players: Iterable[Person] = (),
    ) -> bool:
        """Roda a mensagem: responde, ou chama o handler do comando e fecha o cooldown. Devolve se era comando.

        O handler pode ser `def` ou `async def`. Levantar CommandError vira a resposta de uso (e não conta); devolver
        False não gasta o cooldown; outro erro devolve o cooldown e sobe.
        """
        m = self.match(text, player, now, players)
        if m is None:
            return False

        async def say(t: str) -> None:
            result = reply(t)
            if inspect.isawaitable(result):
                await result

        if not m.is_run:
            for t in m.replies:
                await say(t)
            return True
        reg = self._by_name[m.command or ""]
        ctx = Context(player, m.args, m.command or "", m.alias, m.words, m.rest, say)
        counted = False
        try:
            result = reg.command.handler(ctx)
            if inspect.isawaitable(result):
                result = await result
            counted = result is not False
        except CommandError as err:
            await say(m.usage(str(err)))
        finally:
            m.finish(counted)
        return True


def _chunk_list(names: list[str], footer: str) -> list[str]:
    lines: list[str] = []
    cur = "Comandos:"
    for i, n in enumerate(names):
        token = n + ("," if i < len(names) - 1 else ".")
        nxt = f"{cur} {token}"
        if len(nxt) > MAX_CHAT:
            lines.append(cur)
            cur = token
        else:
            cur = nxt
    if not names:
        cur = "Comandos: nenhum."
    if len(cur + footer) <= MAX_CHAT:
        lines.append(cur + footer)
    else:
        lines += [cur, footer.strip()]
    return lines
