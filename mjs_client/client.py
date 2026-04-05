import aiohttp
import asyncio
from enum import IntEnum
import hashlib
import hmac
import logging
from typing import Callable, Coroutine
from urllib.parse import urljoin
import uuid

from .accident import Accident
from .api import protocol_pb2 as pb
from .api.base import MSRPCChannel, ONCE_HOOK
from .api.rpc import Lobby
from .const import MS_HOST, ENDPOINT, MATCH_SID, MODE_INT
from .exceptions import LoginError, StartUnifiedMatchError, JoinRoomError, PhaseInvalid
from .game.game import Game
from .game.operation import AbstractOperation
from .level import Level
from .room import Room
from .rule import DetailRule, get_default_rule


class ClientPhase(IntEnum):
    BLANK = 0
    BEFORE_LOGIN = 1
    LOBBY = 2
    INGAME = 3
    INROOM = 4


_CLIENT_PHASE_COUNT = 5


def limit(*phases):
    def decor(f):
        async def f_modified(self, *args, **kwargs):
            if self.phase not in phases:
                raise PhaseInvalid(self.phase)
            await f(self, *args, **kwargs)
        return f_modified
    return decor


class MahjongSoulClient:
    def __init__(self):
        self.phase = ClientPhase.BLANK
        self.update_event = asyncio.Event()
        self._events = [asyncio.Event() for i in range(_CLIENT_PHASE_COUNT)]
        self.accidents: asyncio.Queue[Accident] = asyncio.Queue()

        self.ms_host = ""
        self.endpoint = ""
        self.version_to_force = ""
        self.lobby: Lobby | None = None
        self.channel: MSRPCChannel | None = None
        self.account_id: int = 0
        self.account_name: str = ""
        self.account_level: dict[int, Level] = {}
        self.game: Game | None = None
        self.room: Room | None = None

    def _set_phase(self, phase: int):
        self._events[self.phase].clear()
        self._events[phase].set()
        self.phase = phase
        self.update_event.set()

    def add_hook(self, msg_type: str, hook: Callable[[], Coroutine]):
        self.channel.add_hook(msg_type, lambda data: hook())

    async def connect(self, route: int = 2, ms_host: str = MS_HOST, endpoint: str = ENDPOINT, ssl: bool = True):
        async with aiohttp.ClientSession() as session:
            async with session.get(urljoin(ms_host, "/1/version.json"), ssl=ssl) as res:
                version = await res.json()
                # logging.info(f"Version: {version}")
                version = version["version"]
                self.version_to_force = version.replace(".w", "")

        logging.info(f"{route=}")
        chosen_endpoint = endpoint.format(route)
        endpoint_gateway = urljoin(chosen_endpoint, "gateway")
        logging.info(f"Chosen endpoint gateway: {endpoint_gateway}")
        self.channel = MSRPCChannel(endpoint_gateway)
        self.lobby = Lobby(self.channel)
        self.ms_host = ms_host
        self.endpoint = chosen_endpoint

        logging.info(f"{ms_host=}")
        await self.channel.connect(ms_host)
        self._set_phase(ClientPhase.BEFORE_LOGIN)

    def _update_account_level(self, account_pb: pb.Account):
        self.account_level[3] = (Level(level_id=account_pb.level3.id, score=account_pb.level3.score))
        self.account_level[4] = (Level(level_id=account_pb.level.id, score=account_pb.level.score))

    @limit(ClientPhase.BEFORE_LOGIN)
    async def login(self, username: str, password: str):
        uuid_key = str(uuid.uuid1())

        req = pb.ReqLogin(account=username, password=hmac.new(b"lailai", password.encode(), hashlib.sha256).hexdigest(),
                          random_key=uuid_key, gen_access_token=True,
                          client_version_string=f"web-{self.version_to_force}", currency_platforms=[2])
        req.device.is_browser = True
        res = await self.lobby.login(req)
        LoginError.check(res)
        self.account_id = res.account_id
        self._update_account_level(res.account)

        await self.lobby.login_beat(pb.ReqLoginBeat())  # Necessary for starting unified match

        await self.lobby.login_success(pb.ReqCommon())

        self._set_phase(ClientPhase.LOBBY)

    async def _start_game(self, connect_token: str, game_uuid: str, player_count: int, is_east: bool,
                          detail_rule: DetailRule, from_room: bool):
        self.game = Game(self, connect_token, game_uuid, player_count, is_east, detail_rule, from_room)
        await self.game.start()
        self._set_phase(ClientPhase.INGAME)

    @limit(ClientPhase.LOBBY)
    async def start_unified_match(self, level: int, player_count: int, is_east: bool):
        match_sid = MATCH_SID[level][MODE_INT[(player_count, is_east)]]
        res = await self.lobby.start_unified_match(
            pb.ReqStartUnifiedMatch(match_sid=f"1:{match_sid}", client_version_string=f"web-{self.version_to_force}"))
        StartUnifiedMatchError.check(res)

        async def match_game_start_hook(data):
            data_pb = pb.NotifyMatchGameStart.FromString(data)
            await self._start_game(data_pb.connect_token, data_pb.game_uuid, player_count, is_east,
                                   get_default_rule(player_count), False)

        self.channel.add_hook(".lq.NotifyMatchGameStart", match_game_start_hook, ONCE_HOOK)

    @limit(ClientPhase.INGAME)
    async def game_put_operation(self, operation: AbstractOperation):
        await self.game.put_operation(operation)

    @limit(ClientPhase.INGAME)
    async def game_confirm_new_round(self):
        await self.game.confirm_new_round()

    @limit(ClientPhase.INGAME)
    async def return_from_game(self):
        await self.game.game_end_event.wait()
        await self.lobby.log_report(pb.ReqLogReport(success=2, failed=2))
        res_fetch_account_info = await self.lobby.fetch_account_info(pb.ReqAccountInfo(account_id=self.account_id))
        self._update_account_level(res_fetch_account_info.account)
        if self.game.from_room:
            res_fetch_room = await self.lobby.fetch_room(pb.ReqCommon())
            self.room = Room(self, join_room_protobuf=res_fetch_room.room)
            self._set_phase(ClientPhase.INROOM)
        else:
            self._set_phase(ClientPhase.LOBBY)

    @limit(ClientPhase.LOBBY)
    async def create_room(self, player_count: int, is_east: bool, detail_rule: DetailRule = None):
        if player_count not in (3, 4):
            raise ValueError("player_count must be 3 or 4")
        if detail_rule is None:
            detail_rule = get_default_rule(player_count)
        self.room = Room(self, player_count=player_count, is_east=is_east, detail_rule=detail_rule)
        await self.room.create()
        self._set_phase(ClientPhase.INROOM)

    @limit(ClientPhase.INROOM)
    async def room_add_bot(self, position: int):
        await self.room.add_bot(position)

    @limit(ClientPhase.INROOM)
    async def room_start(self):
        await self.room.start()

    @limit(ClientPhase.INROOM)
    async def room_ready(self, ready: bool, switch: bool = False):
        await self.room.ready(ready, switch)

    @limit(ClientPhase.INROOM)
    async def room_kick(self, position: int):
        await self.room.kick(position)

    @limit(ClientPhase.INROOM)
    async def join_room(self, room_id: int):
        res = await self.lobby.join_room(pb.ReqJoinRoom(room_id=room_id,
                                                        client_version_string=f"web-{self.version_to_force}"))
        JoinRoomError.check(res)

        self.room = Room(self, join_room_protobuf=res.room)
        self._set_phase(ClientPhase.INROOM)

    @limit(ClientPhase.INROOM)
    async def leave_room(self):
        await self.lobby.leave_room(pb.ReqCommon())
        await self._call_on_return_from_room()

    async def _call_on_return_from_room(self):
        self._set_phase(ClientPhase.LOBBY)
