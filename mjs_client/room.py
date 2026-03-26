import logging
from typing import Callable
from functools import partial
from sortedcontainers import SortedList
from dataclasses import asdict

from .accident import RoomKicked
from .const import MODE_INT
from .rule import DetailRule, get_mode_int, mode_int_is_east
from .api import protocol_pb2 as pb
from .exceptions import CreateRoomError, AddBotError, ClientError, StartRoomError


class Seat:
    def __init__(self, account_id: int, nickname: str, ready: bool, is_robot:bool=False):
        self.account_id = account_id
        self.nickname = nickname
        self.ready = ready or is_robot
        self.is_robot = is_robot


class Room:
    def __init__(self, client, *, player_count: int = 0, is_east: bool = None, detail_rule: DetailRule = None, join_room_protobuf: pb.Room = None):
        self.client = client

        self._seq = -1
        self._update_queue: SortedList[tuple[Callable, int, tuple]] = SortedList(key=lambda t: t[1])

        if join_room_protobuf is not None:
            self.player_count = join_room_protobuf.max_player_count
            self.seats: list[Seat] = [Seat(0, "", False) for i in range(self.player_count)]
            self.is_east = mode_int_is_east(join_room_protobuf.mode.mode)
            self.detail_rule = DetailRule.from_protobuf(join_room_protobuf.mode.detail_rule)
            self.room_id = join_room_protobuf.room_id
            self._update_seats(join_room_protobuf.persons, join_room_protobuf.robots, join_room_protobuf.positions, join_room_protobuf.owner_id)
            for account_id in join_room_protobuf.ready_list:
                self._update_ready(account_id, True)
            self.created: bool = True
        else:
            assert player_count in (3, 4)
            assert is_east is not None
            assert detail_rule is not None
            self.player_count: int = player_count
            self.seats: list[Seat] = [Seat(0, "", False) for i in range(self.player_count)]
            self.is_east: bool = is_east
            self.detail_rule: DetailRule = detail_rule
            self.room_id: int = 0
            self.owner_id: int = 0
            self.created: bool = False

        self.client.channel.create_hook_field(id(self))
        self.client.channel.add_hook(".lq.NotifyRoomPlayerUpdate", self._room_player_update_hook, id(self))
        self.client.channel.add_hook(".lq.NotifyRoomPlayerReady", self._room_player_ready_hook, id(self))
        self.client.channel.add_hook(".lq.NotifyRoomKickOut", self._room_kick_out_hook, id(self))
        self.client.channel.add_hook(".lq.NotifyRoomGameStart", self._room_game_start_hook, id(self))

    async def _room_game_start_hook(self, data):
        data_pb = pb.NotifyRoomGameStart.FromString(data)
        await self.client._start_game(data_pb.connect_token, data_pb.game_uuid, self.player_count, self.is_east, self.detail_rule, True)

    async def _room_player_update_hook(self, data):
        data = pb.NotifyRoomPlayerUpdate.FromString(data)
        #logging.info(f"{data.seq=}")
        self._update_queue.add((self._update_seats, data.seq, (data.player_list, data.robots, data.positions, data.owner_id)))
        self._flush_queue()

    async def _room_player_ready_hook(self, data):
        data = pb.NotifyRoomPlayerReady.FromString(data)
        self._update_queue.add((self._update_ready, data.seq, (data.account_id, data.ready)))
        self._flush_queue()

    async def _room_kick_out_hook(self, data):
        self.created = False
        self.client.accidents.put(RoomKicked())
        await self.client._call_on_return_from_room()

    def _flush_queue(self):
        #logging.info("Room _flush_queue")
        while self._update_queue:
            #logging.info(f"_flush_queue: {self._update_queue}, {self._seq}")
            func, seq, args = self._update_queue[0]
            if seq == self._seq or self._seq == -1:
                func, seq, args = self._update_queue[0]
                func(*args)
                self._update_queue.pop(0)
                self._seq = seq + 1
                self.client.update_event.set()
            else:
                break

    def _update_seats(self, persons, robots, positions, owner_id=0):
        seat_objects = ({account.account_id: Seat(account.account_id, account.nickname, False) for account in persons} |
                        {account.account_id: Seat(account.account_id, account.nickname, False, True) for account in robots})

        old_positions = [seat.account_id for seat in self.seats]
        diff_indexes = [i for i, (old_id, new_id) in enumerate(zip(old_positions, positions)) if old_id != new_id]
        for diff_idx in diff_indexes:
            new_account_id = positions[diff_idx]
            if new_account_id == 0:
                self.seats[diff_idx] = Seat(0, "", False)
            else:
                self.seats[diff_idx] = seat_objects[new_account_id]
        if owner_id:
            self.owner_id = owner_id

    def _update_ready(self, account_id: int, ready: bool):
        for seat in self.seats:
            if seat.account_id == account_id:
                seat.ready = ready

    def is_owner(self) -> bool:
        return self.owner_id == self.client.account_id

    def all_ready(self) -> bool:
        return all(s.ready for s in self.seats)

    def me(self) -> Seat:
        for s in self.seats:
            if s.account_id == self.client.account_id:
                return s
        raise ClientError("Unexpected fatal error: not found current account in room")

    async def create(self):
        mode_int = MODE_INT[(self.player_count, self.is_east)]
        res = await self.client.lobby.create_room(pb.ReqCreateRoom(player_count=self.player_count, public_live=False,
                                                            client_version_string=f"web-{self.client.version_to_force}",
                                                            pre_rule='',
                                                            mode=pb.GameMode(mode=mode_int, ai=True,
                                                                             detail_rule=pb.GameDetailRule(**asdict(self.detail_rule)))
                                                            ))
        CreateRoomError.check(res)
        self.room_id = res.room.room_id
        self._update_seats(res.room.persons, (), res.room.positions, res.room.owner_id)
        self._update_ready(self.client.account_id, True)
        self.created = True

    async def add_bot(self, position: int):
        res = await self.client.lobby.add_room_robot(pb.ReqAddRoomRobot(position=position))
        AddBotError.check(res)

    async def start(self):
        if not self.all_ready():
            raise StartRoomError("Player not all ready")
        await self.client.lobby.start_room(pb.ReqRoomStart())

    async def ready(self, ready: bool, switch:bool=False):
        if switch:
            ready = not self.me().ready
        await self.client.lobby.ready_play(pb.ReqRoomReady(ready=ready))

    async def kick(self, position: int):
        await self.client.lobby.room_kick_player(pb.ReqRoomKickPlayer(id=self.seats[position].account_id))

    def __del__(self):
        self.client.channel.destroy_hook_field(id(self))
