import asyncio
from urllib.parse import urljoin

from google.protobuf.message import DecodeError

from ..api.base import MSRPCChannel
from ..api.rpc import FastTest
from ..api import protocol_pb2 as pb
from ..rule import DetailRule

from . import action
from .action_prototype_decode import decode
from .action_handler import GameActionHandler
from .operation import AbstractOperation
from .phases import GamePhase


class Game:
    def __init__(self, client, connect_token: str, game_uuid: str, player_count: int, is_east: bool, rule: DetailRule, from_room: bool):
        self.client = client
        self.connect_token = connect_token
        self.game_uuid = game_uuid
        self.player_count = player_count
        self.is_east = is_east
        self.rule = rule
        self.from_room = from_room

        self.action_handler: GameActionHandler | None = None
        self.fasttest: FastTest | None = None
        self.channel: MSRPCChannel | None = None
        self.my_seat: int | None = None
        self.player_names: list[str | None] = []
        self.game_start_event = asyncio.Event()
        self.game_end_event = asyncio.Event()

    async def start(self):
        self.channel = MSRPCChannel(urljoin(self.client.endpoint, "game-gateway-zone"))
        self.fasttest = FastTest(self.channel)
        #self.game_channel.add_hook(".lq.NotifyGameEndResult", lambda data: Game._hook_notify_game_end_result(self, data), id(self))
        await self.channel.connect(self.client.ms_host)
        res_auth = await self.fasttest.auth_game(
            pb.ReqAuthGame(account_id=self.client.account_id, token=self.connect_token,
                   game_uuid=self.game_uuid))

        self.my_seat = res_auth.seat_list.index(self.client.account_id)
        for account_id in res_auth.seat_list:
            for player in res_auth.players:
                if player.account_id == account_id:
                    self.player_names.append(player.nickname)
                    break
            else:
                self.player_names.append("")

        self.action_handler = GameActionHandler(self, self.player_count, self.is_east, self.my_seat)
        self.channel.add_hook(".lq.ActionPrototype", self._hook_action_prototype)
        self.channel.add_hook(".lq.NotifyGameEndResult", self._hook_game_end)
        await self.fasttest.enter_game(pb.ReqCommon())
        #asyncio.create_task(heartbeat(self.game_channel))
        self.action_handler.game_state.phase = GamePhase.STARTING
        self.game_start_event.set()

    async def _hook_action_prototype(self, data):
        action_prototype = pb.ActionPrototype.FromString(data)
        if action_prototype.name not in action.NAME_DICT:
            #logging.warn(f"ActionPrototype {action_prototype.name} not in action.NAME_DICT, change to PlaceHolder")
            self.action_handler.add_action(action.PlaceHolder(action_prototype.step, action_prototype.data))
        else:
            try:
                data_decoded = decode(action_prototype.data)
                data_obj = action.NAME_DICT[action_prototype.name].data_class.FromString(data_decoded)
            except (DecodeError, UnicodeDecodeError):
                sync_res = await self.fasttest.sync_game(pb.ReqSyncGame(round_id="-1", step=1000000))

                for action_prototype_sync in sync_res.game_restore.actions:
                    if action_prototype_sync.step == action_prototype.step:
                        data_decoded = action_prototype_sync.data
                        data_obj = action.NAME_DICT[action_prototype.name].data_class.FromString(data_decoded)
                        break
                else:
                    #logging.warn(f"ActionPrototype {action_prototype.name}, step={action_prototype.step} not found in ResSyncGame! Change to PlaceHolder")
                    self.action_handler.add_action(action.PlaceHolder(action_prototype.step, action_prototype.data))
                    await self.action_handler.update()
                    return

            #logging.info(f"Received {action_prototype.name}:\n {data_obj}")
            self.action_handler.add_action(
                action.NAME_DICT[action_prototype.name](action_prototype.step, data_obj))

        await self.action_handler.update()

    async def _hook_game_end(self, data):
        self.action_handler.end_game(pb.NotifyGameEndResult.FromString(data).result)
        self.game_end_event.set()

    async def put_operation(self, operation: AbstractOperation):
        await operation.perform(self.fasttest)

    async def confirm_new_round(self):
        await self.fasttest.confirm_new_round(pb.ReqCommon())

    def call_on_termination(self):
        if self.channel:
            self.channel.close()

    def __del__(self):
        self.call_on_termination()