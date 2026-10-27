# Gerado de protocol/bot-protocol.schema.json por scripts/generate_types.py. Não edite à mão.

from __future__ import annotations

from typing import Any, Awaitable, Callable, TypeVar, Union

from .types import (
    ReadyMessage,
    ChatMessageEvent,
    MatchEndedEvent,
    MatchEventEvent,
    MatchStartedEvent,
    PlayerJoinedEvent,
    PlayerLeftEvent,
    RoomConfigEvent,
    RoomLiveEvent,
    RoomOffEvent,
    RuleFiredEvent,
    ScriptLogEvent,
    ScriptStoppedEvent,
)

H = TypeVar('H', bound=Callable[..., Any])


class EventDecorators:
    """Um decorador por evento da sala, com o tipo do evento no argumento do handler."""

    def on(self, event: str, handler: H | None = None) -> Any:  # implementado no RoomBot
        raise NotImplementedError

    def on_ready(self, handler: Callable[[ReadyMessage], Union[None, Awaitable[None]]]) -> Callable[[ReadyMessage], Union[None, Awaitable[None]]]:
        """Escuta o ready: a auth foi aceita (a cada conexão, inclusive depois de reconectar)."""
        return self.on('ready', handler)

    def on_room_live(self, handler: Callable[[RoomLiveEvent], Union[None, Awaitable[None]]]) -> Callable[[RoomLiveEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'room.live'; serve de decorador."""
        return self.on('room.live', handler)

    def on_room_off(self, handler: Callable[[RoomOffEvent], Union[None, Awaitable[None]]]) -> Callable[[RoomOffEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'room.off'; serve de decorador."""
        return self.on('room.off', handler)

    def on_room_config(self, handler: Callable[[RoomConfigEvent], Union[None, Awaitable[None]]]) -> Callable[[RoomConfigEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'room.config'; serve de decorador."""
        return self.on('room.config', handler)

    def on_player_joined(self, handler: Callable[[PlayerJoinedEvent], Union[None, Awaitable[None]]]) -> Callable[[PlayerJoinedEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'player.joined'; serve de decorador."""
        return self.on('player.joined', handler)

    def on_player_left(self, handler: Callable[[PlayerLeftEvent], Union[None, Awaitable[None]]]) -> Callable[[PlayerLeftEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'player.left'; serve de decorador."""
        return self.on('player.left', handler)

    def on_chat_message(self, handler: Callable[[ChatMessageEvent], Union[None, Awaitable[None]]]) -> Callable[[ChatMessageEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'chat.message'; serve de decorador."""
        return self.on('chat.message', handler)

    def on_match_started(self, handler: Callable[[MatchStartedEvent], Union[None, Awaitable[None]]]) -> Callable[[MatchStartedEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'match.started'; serve de decorador."""
        return self.on('match.started', handler)

    def on_match_event(self, handler: Callable[[MatchEventEvent], Union[None, Awaitable[None]]]) -> Callable[[MatchEventEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'match.event'; serve de decorador."""
        return self.on('match.event', handler)

    def on_match_ended(self, handler: Callable[[MatchEndedEvent], Union[None, Awaitable[None]]]) -> Callable[[MatchEndedEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'match.ended'; serve de decorador."""
        return self.on('match.ended', handler)

    def on_rule_fired(self, handler: Callable[[RuleFiredEvent], Union[None, Awaitable[None]]]) -> Callable[[RuleFiredEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'rule.fired'; serve de decorador."""
        return self.on('rule.fired', handler)

    def on_script_log(self, handler: Callable[[ScriptLogEvent], Union[None, Awaitable[None]]]) -> Callable[[ScriptLogEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'script.log'; serve de decorador."""
        return self.on('script.log', handler)

    def on_script_stopped(self, handler: Callable[[ScriptStoppedEvent], Union[None, Awaitable[None]]]) -> Callable[[ScriptStoppedEvent], Union[None, Awaitable[None]]]:
        """Escuta o evento 'script.stopped'; serve de decorador."""
        return self.on('script.stopped', handler)
