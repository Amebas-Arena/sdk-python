"""Os casos compartilhados (protocol/commands.conformance.json): os mesmos do script do painel, do @amebas/sdk e do sdk-go."""

import json
from pathlib import Path

import pytest

from amebas.commands import Command, CommandPlayer, Commands, Person

FIXTURE = json.loads((Path(__file__).parent.parent / "protocol" / "commands.conformance.json").read_text(encoding="utf-8"))


def _person(p: dict) -> Person:
    return Person(p["id"], p["nick"], p["accountId"])


def _player(p: dict) -> CommandPlayer:
    return CommandPlayer(p["id"], p["nick"], p["accountId"], p["role"])


def _normalize(args: dict) -> dict:
    return {k: ({"id": v.id, "nick": v.nick, "accountId": v.account_id} if isinstance(v, Person) else v) for k, v in args.items()}


def _command(name: str, define: dict) -> Command:
    cooldown = define.get("cooldown")
    if isinstance(cooldown, dict):
        cooldown = {("exempt_staff" if k == "exemptStaff" else k): v for k, v in cooldown.items()}
    return Command(
        name=name,
        handler=lambda ctx: None,
        aliases=tuple(define.get("aliases", ())),
        description=define.get("description", ""),
        hidden=define.get("hidden", False),
        args=define.get("args", {}),
        cooldown=cooldown,
        permission=define.get("permission"),
        messages=define.get("messages"),
    )


@pytest.mark.parametrize("case", FIXTURE["cases"], ids=[c["name"] for c in FIXTURE["cases"]])
async def test_case(case):
    commands = Commands()
    defaults = dict(case.get("defaults", {}))
    if defaults:
        commands.defaults(
            cooldown=defaults.get("cooldown"), permission=defaults.get("permission"),
            messages=defaults.get("messages"), prefix=defaults.get("prefix"), help=defaults.get("help"),
        )
    ran: dict = {}
    result = [None]

    def handler(ctx):
        ran["command"], ran["args"] = ctx.command, _normalize(ctx.args)
        return result[0]

    for c in case["commands"]:
        cmd = _command(c["name"], c.get("define", {}))
        cmd.handler = handler
        commands.add(cmd)
    people = [_person(FIXTURE["players"][k]) for k in case.get("players", [])]
    at = 0
    for step in case["steps"]:
        at = step.get("at", at)
        ran.clear()
        result[0] = False if step.get("result") is False else None
        replies: list[str] = []
        handled = await commands.dispatch(
            step["text"], _player(FIXTURE["players"][step["as"]]), replies.append, now=at / 1000, players=people
        )
        where = f"{step['as']}: {step['text']}"
        expect = step["expect"]
        if expect.get("ignore"):
            assert not handled, where
        elif "replies" in expect:
            assert replies == expect["replies"], where
            assert not ran, where
        else:
            assert ran == {"command": expect["run"], "args": expect["args"]}, where
            assert replies == [], where
