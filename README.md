# amebas

SDK oficial do **bot de sala** do [Amebas Arena](https://github.com/Amebas-Arena) em Python: conecta no WebSocket da
sala, entrega os eventos e dá um sistema de **comandos de chat** pronto (`!gols 5`) com argumentos, permissão e
cooldown. `asyncio`, Python 3.10+, tipado.

```sh
pip install amebas
```

```python
import asyncio
import random

from amebas import RoomBot

bot = RoomBot("https://SEU-SITE/api", room_id="ID_DA_SALA", key="amb_...")

@bot.on_player_joined
async def oi(e):
    await bot.chat(f"Oi, {e['player']['nick']}!")

@bot.command("regras")
async def regras(ctx):
    await ctx.reply("Sem xingar e joga limpo.")

@bot.command("dado", args={"lados": "int:2..100=6"}, cooldown=5)
async def dado(ctx):
    await ctx.reply(f"Tirou {random.randint(1, ctx.args.lados)}")  # ctx.args.lados é int

asyncio.run(bot.run())  # fica no ar e reconecta sozinho
```

A **chave** (`amb_...`) você cria no painel da comunidade, com o escopo `rooms:control`. O `room_id` é o id da sala
hospedada. Nunca coloque a chave num site: ela dá controle total da sala.

## Eventos

`@bot.on_<evento>` entrega o evento como `TypedDict` (o editor completa as chaves). Ou `@bot.on("chat.message")`.

| Decorador | Quando |
|---|---|
| `on_ready` | a auth foi aceita (também depois de reconectar); traz a sala e quem está nela |
| `on_player_joined` / `on_player_left` | alguém entrou / saiu (`reason`: left, dropped, kicked, banned) |
| `on_chat_message` | mensagem no chat (`player` é `None` quando é do sistema) |
| `on_match_started` / `on_match_event` / `on_match_ended` | partida: começou, lance (gol, cartão...), terminou com a súmula |
| `on_room_live` / `on_room_off` / `on_room_config` | a sala ligou, desligou ou mudou de config |
| `on_rule_fired` / `on_script_log` / `on_script_stopped` | regras sem código e script da sala |
| `on("event")` | qualquer um dos eventos da sala |

Os handlers podem ser `def` ou `async def`. Se um deles levantar exceção, o erro vai pro `logging` (logger `amebas`) e o
bot continua.

## Comandos da sala

```python
await bot.chat("Bem-vindos!")
await bot.kick(player_id)
await bot.start()
await bot.send({"type": "config", "config": {"time": 180}})  # qualquer comando do protocolo, tipado
```

Todo comando espera a resposta da sala: volta se deu certo e levanta `RoomBotError` (`err.code`: `permission`,
`invalid`, `rate_limited`...) se foi recusado. Limite: 20 comandos de cara e 5 por segundo.

## Comandos de chat (`!gols 5`)

```python
@bot.command("gols", args={"n": "int:1..20"}, cooldown=10, permission="staff")
async def gols(ctx):
    await ctx.reply(f"Top {ctx.args.n}: ...")
```

Argumento errado, cooldown e permissão **respondem sozinhos** no chat, sem você escrever nada:

```
Ana:  !gols 99
Bot:  Valor inválido pra n: um número inteiro de 1 a 20. Uso: !gols <n>
Ana:  !gols 5          (e de novo, 3 s depois)
Bot:  Espere 7s pra usar !gols de novo.
```

### A define

São parâmetros do `@bot.command`. Guarde num `dict` e espalhe:

```python
STAFF = dict(permission="staff", cooldown=30)

@bot.command("silencio", **STAFF, args={"motivo": "rest?"})
async def silencio(ctx):
    await ctx.reply("Silêncio!")
```

| Parâmetro | O que faz |
|---|---|
| `args` | os argumentos, em ordem: `{"nome": "tipo"}` |
| `cooldown` | segundos por pessoa, ou `{"player": 10, "room": 3, "exempt_staff": False}` |
| `permission` | `"all"` (padrão), `"staff"` ou `"owner"` |
| `aliases` | outros nomes: `["g", "artilharia"]` |
| `description` | a linha do `!ajuda` |
| `hidden` | fora do `!ajuda` |
| `messages` | troca as respostas prontas (`usage`, `cooldown`, `permission`) |
| `parse` | troca o parser padrão |

### Tipos de argumento

`"tipo[:faixa][?|=padrão]"` — o valor chega em `ctx.args.nome` (ou `ctx.args["nome"]`).

| Escrito | Aceita | Valor |
|---|---|---|
| `"int"`, `"int:1..20"`, `"int:1.."`, `"int:..20"` | inteiro, com faixa | `int` |
| `"number:0..1"` | decimal (`1,5` ou `1.5`) | `float` |
| `"text"`, `"text:3..16"` | uma palavra (a faixa é o tamanho) | `str` |
| `"rest"` | o resto da linha (tem que ser o último) | `str` |
| `"bool"` | sim/não | `bool` |
| `"team"` | `a` ou `b` | `"a"` / `"b"` |
| `"player"` | `#id`, `@nick`, nick ou começo do nick | `Person(id, nick, account_id)` |
| `"azul\|vermelho"` | uma das opções | `str` |
| `"int:1..?"` | opcional | `int` ou `None` |
| `"int:1..20=5"` | com padrão | `int` |

### Padrões pra todos os comandos

```python
bot.command_defaults(cooldown=3, permission="all", prefix="!")
```

A define de cada comando sobrescreve o padrão. O `!ajuda` (também `!help` e `!comandos`) já vem pronto e lista só o que a
pessoa pode usar; `command_defaults(help=False)` desliga.

### Parser próprio

```python
from amebas import CommandError

def parse_placar(*, words, **_):
    try:
        casa, fora = map(int, words[:2])
    except ValueError:
        raise CommandError("Use dois números") from None
    return {"casa": casa, "fora": fora}

@bot.command("placar", parse=parse_placar)
async def placar(ctx):
    await ctx.reply(f"{ctx.args.casa} x {ctx.args.fora}")
```

`CommandError` vira a resposta de uso, e o handler não roda. **Devolver `False`** do handler diz "não contou": o cooldown
não começa. Tudo isso está especificado em [COMANDOS.md](https://github.com/Amebas-Arena/protocol/blob/main/COMANDOS.md),
igual nos SDKs de TypeScript e Go.

## Quando algo falha

| Situação | O que acontece |
|---|---|
| a conexão caiu | reconecta sozinho (espera de 1 s dobrando até 30 s) |
| chave errada, sem escopo, sala de outra comunidade | **não** reconecta: `run()` levanta `RoomBotError` com o `code` |
| comando antes do `ready` | `RoomBotError` `not_connected`: "espere o ready" |
| erro de define (tipo que não existe, faixa torta) | `DefinitionError` na hora de registrar, dizendo o que está errado |

Opções do `RoomBot`: `reconnect=False`, `initial_delay`, `max_delay`, `max_attempts`, `command_timeout`.

## Tipos gerados

Os tipos do protocolo (`ChatMessageEvent`, `RoomCommand`...) são **gerados** de `protocol/bot-protocol.schema.json`, o
schema do servidor ([Amebas-Arena/protocol](https://github.com/Amebas-Arena/protocol)). Para atualizar: copie o schema
novo pra `protocol/` e rode `uv run --group dev python scripts/generate_types.py`.

## Desenvolvimento

```sh
uv run --group dev pytest        # cliente + os casos de conformidade dos comandos
uv build                         # wheel e sdist em dist/
```

MIT.
