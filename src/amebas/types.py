# Gerado de protocol/bot-protocol.schema.json por scripts/generate_types.py. Não edite à mão: o schema é a fonte.

from __future__ import annotations

from typing import Literal, TypeAlias

from typing_extensions import NotRequired, TypedDict  # noqa: F401


class AdminCommand(TypedDict):
    type: Literal['admin']
    playerId: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """
    admin: bool


class AuthMessage(TypedDict):
    type: Literal['auth']
    key: str


class AutoCommand(TypedDict):
    type: Literal['auto']


class BanCommand(TypedDict):
    type: Literal['ban']
    playerId: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """
    scope: NotRequired[Literal['room', 'community']]


class BotCommand(TypedDict):
    type: Literal['bot']
    team: Literal['a', 'b']
    delta: Literal[1, -1]
    slot: NotRequired[int]


class BotsCommand(TypedDict):
    type: Literal['bots']
    action: Literal['fill', 'clear']


class CaptainCommand(TypedDict):
    type: Literal['captain']
    team: Literal['a', 'b']
    playerId: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """


class ChatCommand(TypedDict):
    type: Literal['chat']
    text: str


class ConfirmCommand(TypedDict):
    type: Literal['confirm']


class ErrorMessage(TypedDict):
    type: Literal['error']
    code: str
    message: str


class FinishCommand(TypedDict):
    type: Literal['finish']


class Welcome(TypedDict):
    text: str


Message: TypeAlias = str


class Notices(TypedDict):
    everyMinutes: int
    messages: list[Message]


Word: TypeAlias = str


class ChatRules(TypedDict):
    words: list[Word]
    action: Literal['mute', 'kick']


class Afk(TypedDict):
    seconds: int
    action: Literal['spectate', 'kick']


class HostBot(TypedDict):
    welcome: NotRequired[Welcome]
    notices: NotRequired[Notices]
    chatRules: NotRequired[ChatRules]
    afk: NotRequired[Afk]


class Live(TypedDict):
    code: str
    address: str | None
    players: int


class Gameplay(TypedDict):
    maxSpeed: NotRequired[float]
    accelTime: NotRequired[float]
    turning: NotRequired[float]
    aimAssist: NotRequired[float]
    controlSpin: NotRequired[float]
    ballMass: NotRequired[float]
    ballFriction: NotRequired[float]
    ballAirFriction: NotRequired[float]
    ballBounce: NotRequired[float]
    ballSize: NotRequired[float]
    kickPower: NotRequired[float]
    gravity: NotRequired[float]
    playerSize: NotRequired[float]


class HostedRoomConfig(TypedDict):
    preset: NotRequired[str]
    mode: NotRequired[
        Literal[
            'football', 'penalty', 'volleyball', 'ctf', 'dodgeball', 'tenman', 'race'
        ]
    ]
    modeParams: NotRequired[dict[str, float | bool | str]]
    format: NotRequired[
        Literal['open', 'queue', 'everyone', 'rounds', 'manual', 'knockout']
    ]
    formatParams: NotRequired[dict[str, float | bool | str]]
    map: NotRequired[str]
    communityMap: NotRequired[str]
    time: NotRequired[int]
    goals: NotRequired[int]
    teamSize: NotRequired[int]
    keepers: NotRequired[bool]
    goalkeeper: NotRequired[int]
    ball: NotRequired[str]
    gameplay: NotRequired[Gameplay]


class Gameplay1(TypedDict):
    maxSpeed: NotRequired[float]
    accelTime: NotRequired[float]
    turning: NotRequired[float]
    aimAssist: NotRequired[float]
    controlSpin: NotRequired[float]
    ballMass: NotRequired[float]
    ballFriction: NotRequired[float]
    ballAirFriction: NotRequired[float]
    ballBounce: NotRequired[float]
    ballSize: NotRequired[float]
    kickPower: NotRequired[float]
    gravity: NotRequired[float]
    playerSize: NotRequired[float]


class HostedRoomConfigInput(TypedDict):
    preset: NotRequired[str]
    mode: NotRequired[
        Literal[
            'football', 'penalty', 'volleyball', 'ctf', 'dodgeball', 'tenman', 'race'
        ]
    ]
    modeParams: NotRequired[dict[str, float | bool | str]]
    format: NotRequired[
        Literal['open', 'queue', 'everyone', 'rounds', 'manual', 'knockout']
    ]
    formatParams: NotRequired[dict[str, float | bool | str]]
    map: NotRequired[str]
    communityMap: NotRequired[str]
    time: NotRequired[int]
    goals: NotRequired[int]
    teamSize: NotRequired[int]
    keepers: NotRequired[bool]
    goalkeeper: NotRequired[int]
    ball: NotRequired[str]
    gameplay: NotRequired[Gameplay1]


class KickCommand(TypedDict):
    type: Literal['kick']
    playerId: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """


class KnockoutCommand(TypedDict):
    type: Literal['knockout']
    action: Literal['lock', 'reset']


class LivePlayer(TypedDict):
    id: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """
    nick: str
    accountId: str | None
    place: Literal['a', 'b', 'stands']
    admin: bool
    connection: Literal['ok', 'reconnecting', 'afk']


class Score(TypedDict):
    a: int
    b: int


class LiveRoom(TypedDict):
    code: str
    address: str | None
    phase: Literal['stopped', 'playing', 'paused']
    score: Score
    mode: str
    map: str
    players: list[LivePlayer]


class LockCommand(TypedDict):
    type: Literal['lock']
    locked: bool


class Player(TypedDict):
    accountId: str | None
    nick: str
    team: Literal['a', 'b']
    outcome: Literal['win', 'loss', 'draw'] | None
    stats: dict[str, float]


class Match(TypedDict):
    id: str
    room: str
    hostedRoomId: str | None
    mode: str
    format: str | None
    map: str | None
    scoreA: int
    scoreB: int
    durationSeconds: int
    playedAt: int
    rules: NotRequired[bool]
    players: list[Player]


class MatchEndedEvent(TypedDict):
    type: Literal['match.ended']
    roomId: str
    at: int
    match: Match


class MatchStartedEvent(TypedDict):
    type: Literal['match.started']
    roomId: str
    at: int
    mode: str
    map: str


class MoveCommand(TypedDict):
    type: Literal['move']
    playerId: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """
    to: Literal['a', 'b', 'stands']
    slot: NotRequired[int]


class MuteCommand(TypedDict):
    type: Literal['mute']
    playerId: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """
    muted: NotRequired[bool]


class PauseCommand(TypedDict):
    type: Literal['pause']
    paused: NotRequired[bool]


class PickCommand(TypedDict):
    type: Literal['pick']
    playerId: NotRequired[int]
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """
    number: NotRequired[int]
    keyword: NotRequired[Literal['top', 'bottom', 'random']]


class PlayerRef(TypedDict):
    id: int
    """
    O id do jogador nesta sala, informado nos eventos e no estado ao vivo. O id muda se o jogador sair e voltar.
    """
    nick: str
    accountId: str | None


class RestartCommand(TypedDict):
    type: Literal['restart']


class ResultMessage(TypedDict):
    type: Literal['result']
    ref: NotRequired[str]
    ok: bool
    code: NotRequired[str]
    message: NotRequired[str]


class RoomConfigEvent(TypedDict):
    type: Literal['room.config']
    roomId: str
    at: int
    name: str
    config: HostedRoomConfig


class RoomLiveEvent(TypedDict):
    type: Literal['room.live']
    roomId: str
    at: int
    code: str
    address: str | None


class RoomOffEvent(TypedDict):
    type: Literal['room.off']
    roomId: str
    at: int
    reason: Literal['released', 'empty', 'server_lost', 'failed']


class RoomScript(TypedDict):
    source: str
    enabled: bool


class RuleAction1(TypedDict):
    type: Literal['chat']
    text: str


class RuleAction2(TypedDict):
    type: Literal['reply']
    text: str


class RuleAction3(TypedDict):
    type: Literal['spectate']


class RuleAction4(TypedDict):
    type: Literal['mute']


class RuleAction5(TypedDict):
    type: Literal['kick']


class RuleAction6(TypedDict):
    type: Literal['start']


class RuleAction7(TypedDict):
    type: Literal['stop']


class RuleAction8(TypedDict):
    type: Literal['finish']


class RuleAction9(TypedDict):
    type: Literal['pause']
    paused: NotRequired[bool]


class RuleAction10(TypedDict):
    type: Literal['config']
    mode: NotRequired[
        Literal[
            'football', 'penalty', 'volleyball', 'ctf', 'dodgeball', 'tenman', 'race'
        ]
    ]
    map: NotRequired[str]
    time: NotRequired[int]
    goals: NotRequired[int]


class RuleAction11(TypedDict):
    type: Literal['bots']
    action: Literal['fill', 'clear']


class Colors(TypedDict):
    base: str
    second: str


class RuleAction12(TypedDict):
    type: Literal['team']
    team: Literal['a', 'b']
    name: NotRequired[str]
    kit: NotRequired[str]
    colors: NotRequired[Colors]


RuleAction: TypeAlias = (
    RuleAction1
    | RuleAction2
    | RuleAction3
    | RuleAction4
    | RuleAction5
    | RuleAction6
    | RuleAction7
    | RuleAction8
    | RuleAction9
    | RuleAction10
    | RuleAction11
    | RuleAction12
)


RuleCondition1 = TypedDict(
    'RuleCondition1',
    {
        'type': Literal['player.staff'],
        'is': bool,
    },
    closed=True,
)


RuleCondition2 = TypedDict(
    'RuleCondition2',
    {
        'type': Literal['player.account'],
        'is': bool,
    },
    closed=True,
)


class RuleCondition3(TypedDict):
    type: Literal['player.place']
    place: Literal['field', 'a', 'b', 'stands']


class RuleCondition4(TypedDict):
    type: Literal['people']
    min: NotRequired[int]
    max: NotRequired[int]


RuleCondition5 = TypedDict(
    'RuleCondition5',
    {
        'type': Literal['phase'],
        'in': list[Literal['stopped', 'playing', 'paused']],
    },
    closed=True,
)


class RuleCondition6(TypedDict):
    type: Literal['score']
    of: Literal['a', 'b', 'total', 'diff']
    min: NotRequired[int]
    max: NotRequired[int]


RuleCondition7 = TypedDict(
    'RuleCondition7',
    {
        'type': Literal['mode'],
        'in': list[
            Literal[
                'football',
                'penalty',
                'volleyball',
                'ctf',
                'dodgeball',
                'tenman',
                'race',
            ]
        ],
    },
    closed=True,
)


InItem: TypeAlias = str


RuleCondition8 = TypedDict(
    'RuleCondition8',
    {
        'type': Literal['map'],
        'in': list[InItem],
    },
    closed=True,
)


RuleCondition: TypeAlias = (
    RuleCondition1
    | RuleCondition2
    | RuleCondition3
    | RuleCondition4
    | RuleCondition5
    | RuleCondition6
    | RuleCondition7
    | RuleCondition8
)


class Rule1(TypedDict):
    id: str
    name: str


class Action(TypedDict):
    type: str
    ok: bool
    message: NotRequired[str]


class RuleFiredEvent(TypedDict):
    type: Literal['rule.fired']
    roomId: str
    at: int
    rule: Rule1
    trigger: str
    player: PlayerRef | None
    depth: int
    actions: list[Action]


class RuleTrigger1(TypedDict):
    type: Literal['room.live']


class RuleTrigger2(TypedDict):
    type: Literal['player.joined']


class RuleTrigger3(TypedDict):
    type: Literal['player.left']


class RuleTrigger4(TypedDict):
    type: Literal['chat.command']
    command: str
    hide: NotRequired[bool]


class RuleTrigger5(TypedDict):
    type: Literal['match.started']


class RuleTrigger6(TypedDict):
    type: Literal['match.ended']


class RuleTrigger7(TypedDict):
    type: Literal['match.event']
    event: Literal[
        'Goal',
        'Save',
        'Post',
        'PenaltyKick',
        'Out',
        'Point',
        'Eliminated',
        'Revived',
        'Frozen',
        'Unfrozen',
        'FlagTaken',
        'FlagCaptured',
        'FlagDropped',
        'Block',
        'Fault',
        'Foul',
        'Card',
        'LapCompleted',
        'Finished',
        'RoundStart',
        'RoundEnd',
    ]
    team: NotRequired[Literal['a', 'b']]


class RuleTrigger8(TypedDict):
    type: Literal['score.reached']
    goals: int
    team: NotRequired[Literal['a', 'b']]


class RuleTrigger9(TypedDict):
    type: Literal['time.passed']
    seconds: int


class RuleTrigger10(TypedDict):
    type: Literal['every']
    minutes: int


RuleTrigger: TypeAlias = (
    RuleTrigger1
    | RuleTrigger2
    | RuleTrigger3
    | RuleTrigger4
    | RuleTrigger5
    | RuleTrigger6
    | RuleTrigger7
    | RuleTrigger8
    | RuleTrigger9
    | RuleTrigger10
)


class ScriptLogEvent(TypedDict):
    type: Literal['script.log']
    roomId: str
    at: int
    text: str


class ScriptStoppedEvent(TypedDict):
    type: Literal['script.stopped']
    roomId: str
    at: int
    reason: Literal[
        'compile', 'runtime', 'time', 'memory', 'budget', 'actions', 'private', 'ranked'
    ]
    message: str


class ShuffleCommand(TypedDict):
    type: Literal['shuffle']


class StartCommand(TypedDict):
    type: Literal['start']


class StopCommand(TypedDict):
    type: Literal['stop']


class Colors1(TypedDict):
    base: str
    second: str


class TeamCommand(TypedDict):
    type: Literal['team']
    team: Literal['a', 'b']
    name: NotRequired[str]
    kit: NotRequired[str]
    colors: NotRequired[Colors1]


class Colors2(TypedDict):
    base: str
    second: str


class TeamStyle(TypedDict):
    name: str
    kit: str
    colors: NotRequired[Colors2]


class ChatMessageEvent(TypedDict):
    type: Literal['chat.message']
    roomId: str
    at: int
    player: PlayerRef | None
    text: str
    role: NotRequired[Literal['owner', 'staff', 'player']]


class ConfigCommand(TypedDict):
    type: Literal['config']
    config: HostedRoomConfigInput
    name: NotRequired[str]
    isPublic: NotRequired[bool]
    password: NotRequired[str | None]


class MatchEventEvent(TypedDict):
    type: Literal['match.event']
    roomId: str
    at: int
    event: Literal[
        'Goal',
        'Save',
        'Post',
        'PenaltyKick',
        'Out',
        'Point',
        'Eliminated',
        'Revived',
        'Frozen',
        'Unfrozen',
        'FlagTaken',
        'FlagCaptured',
        'FlagDropped',
        'Block',
        'Fault',
        'Foul',
        'Card',
        'LapCompleted',
        'Finished',
        'RoundStart',
        'RoundEnd',
    ]
    player: PlayerRef | None
    team: Literal['a', 'b'] | None


class PlayerJoinedEvent(TypedDict):
    type: Literal['player.joined']
    roomId: str
    at: int
    player: PlayerRef
    players: int
    """
    quantas pessoas ficaram na sala
    """


class PlayerLeftEvent(TypedDict):
    type: Literal['player.left']
    roomId: str
    at: int
    player: PlayerRef
    reason: Literal['left', 'dropped', 'kicked', 'banned']
    players: int
    """
    quantas pessoas ficaram na sala
    """


RoomCommand: TypeAlias = (
    ChatCommand
    | KickCommand
    | BanCommand
    | MuteCommand
    | MoveCommand
    | TeamCommand
    | CaptainCommand
    | AdminCommand
    | StartCommand
    | StopCommand
    | FinishCommand
    | PauseCommand
    | RestartCommand
    | AutoCommand
    | ShuffleCommand
    | PickCommand
    | ConfirmCommand
    | KnockoutCommand
    | BotCommand
    | BotsCommand
    | LockCommand
    | ConfigCommand
)


RoomEvent: TypeAlias = (
    RoomLiveEvent
    | RoomOffEvent
    | RoomConfigEvent
    | PlayerJoinedEvent
    | PlayerLeftEvent
    | ChatMessageEvent
    | MatchStartedEvent
    | MatchEventEvent
    | MatchEndedEvent
    | RuleFiredEvent
    | ScriptLogEvent
    | ScriptStoppedEvent
)


class RoomTeams(TypedDict):
    """
    O uniforme do time da casa (a) e o do time visitante (b).
    """

    a: TeamStyle
    b: TeamStyle


Rule = TypedDict(
    'Rule',
    {
        'id': str,
        'name': str,
        'enabled': bool,
        'cooldownSeconds': NotRequired[int],
        'when': RuleTrigger,
        'if': list[RuleCondition],
        'do': list[RuleAction],
    },
    closed=True,
)


ClientMessage: TypeAlias = AuthMessage | RoomCommand
"""
O que o bot manda: a auth (primeira mensagem) e, depois dela, comandos. Todo comando aceita um campo ref (texto até 64), que volta no result dele (x-amebas-bot.commandRef).
"""


RoomRules: TypeAlias = list[Rule]


class HostedRoom(TypedDict):
    id: str
    communityId: str
    """
    Slug da comunidade, definido na criação e imutável depois dela.
    """
    code: str
    """
    Código fixo da sala: o id da comunidade, um hífen e um apelido de 1 a 16 letras minúsculas, números e hífen.
    """
    name: str
    isPublic: bool
    hasPassword: bool
    maxPlayers: int
    config: HostedRoomConfig
    plan: Literal['simple', 'full']
    paidUntil: int | None
    alwaysOn: bool
    desired: Literal['on', 'off']
    status: Literal['off', 'starting', 'live']
    live: NotRequired[Live | None]
    hostBot: NotRequired[HostBot | None]
    teams: NotRequired[RoomTeams | None]
    rules: NotRequired[RoomRules | None]
    script: NotRequired[RoomScript | None]
    createdAt: int
    updatedAt: int


class ReadyMessage(TypedDict):
    type: Literal['ready']
    room: HostedRoom
    live: LiveRoom | None


ServerMessage: TypeAlias = ReadyMessage | ResultMessage | ErrorMessage | RoomEvent
"""
O que a API manda: ready (auth aceita), result (de cada comando), error e os eventos da sala.
"""


AmebasBotProtocol: TypeAlias = ClientMessage | ServerMessage
"""
Protocolo do bot de sala do Amebas Arena: WebSocket JSON em /v1/rooms/{roomId}/bot. Gerado de packages/protocol (pnpm --filter @amebas/bot-protocol generate); não edite à mão.
"""
