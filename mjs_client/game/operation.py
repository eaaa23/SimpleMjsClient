from typing import Self

from .action import GameActionMessage
from ..api import protocol_pb2 as pb
from ..api.rpc import FastTest
from ..const import OperationType

from .gamestate import GameState
from .tiles_util import turn0to5


class AbstractOperation:
    code: OperationType = -1

    async def perform(self, fasttest: FastTest):
        await fasttest.input_operation(pb.ReqSelfOperation(type=self.code))

    @classmethod
    def get_possible_operations(cls, data: GameActionMessage, operation: pb.OptionalOperation,
                                game_state: GameState) -> list[Self]:
        """
        Get all possible operations of this class with a specific ActionXXX protobuf data.
        :return: list[AbstractOperation]

        Protocol (rules) of:
        1. Return value matches type list[Self], and it's never an empty list.
        2. If any operation has the `cancel_operation` attribute and cancel_operation=True,
            it will appear at the last item of return value (retval[-1]).
        """
        return [cls()]

    def __str__(self):
        return f"{self.__class__.__name__}()"

    def __repr__(self):
        return self.__str__()


class AbstractPlayTile(AbstractOperation):
    def __init__(self, tile: str, is_moqie: bool):
        self.tile = tile
        self.is_moqie = is_moqie

    async def perform(self, fasttest: FastTest):
        await fasttest.input_operation(pb.ReqSelfOperation(type=self.code, tile=self.tile, moqie=self.is_moqie))

    def __str__(self):
        return f"{self.__class__.__name__}(tile={self.tile}, is_moqie={self.is_moqie})"


class AbstractCancellableOperation(AbstractOperation):
    def __init__(self, cancel_operation: bool = False):
        self.cancel_operation = cancel_operation


class AbstractCallOperation(AbstractCancellableOperation):
    is_self_operation: bool = False

    def __init__(self, tile: str, combination: list[str], index: int, cancel_operation=False):
        super().__init__(cancel_operation)
        self.tile = tile
        self.combination = combination
        self._index = index

    async def perform(self, fasttest: FastTest):
        if self.is_self_operation:
            await fasttest.input_operation(pb.ReqSelfOperation(type=self.code, index=self._index))
        else:
            await fasttest.input_chi_peng_gang(pb.ReqChiPengGang(type=self.code, index=self._index,
                                                                 cancel_operation=self.cancel_operation))

    @classmethod
    def get_possible_operations(cls, data: GameActionMessage, operation: pb.OptionalOperation,
                                game_state: GameState) -> list[Self]:
        tile = data.tile if hasattr(data, "tile") else ""
        retval = [cls(tile, combination.split("|"), index) for index, combination in enumerate(operation.combination)]
        if not cls.is_self_operation:
            retval.append(cls("", [], 0, cancel_operation=True))
        return retval

    def __str__(self):
        return (f"{type(self).__name__}"
                f"(tile={self.tile}, combination={self.combination}, cancel_op={self.cancel_operation})")


class Tsumo(AbstractCancellableOperation):
    code = OperationType.TSUMO
    """
    @classmethod
    def get_possible_operations(cls, data, operation: pb.OptionalOperation, game_state: GameState) -> list:
        if game_state.player_liqis[game_state.my_seat]:
            # After riichi, allowing user to give up tsumo and discard the tile out is important
            return [cls(cancel_operation=False), cls(cancel_operation=True)]
        else:
            # However, without riichi, user can PlayTile, so there's no need.
            return [cls(cancel_operation=False)]
    """


class JiuZhongJiuPai(AbstractOperation):
    code = OperationType.JIUZHONGJIUPAI


class BaBei(AbstractPlayTile):
    code = OperationType.BABEI

    @classmethod
    def get_possible_operations(cls, data: GameActionMessage, operation: pb.OptionalOperation,
                                game_state: GameState) -> list[Self]:
        retval = []
        if game_state.my_hand[-1] == '4z':
            retval.append(cls("", True))
        if '4z' in game_state.my_hand[:-1]:
            retval.append(cls("", False))
        return retval


class PlayTile(AbstractPlayTile):
    code = OperationType.PLAY_TILE

    @classmethod
    def get_possible_operations(cls, data: GameActionMessage, operation: pb.OptionalOperation,
                                game_state: GameState) -> list[Self]:
        # When operation is PlayTile, operation.combination means tiles unable to play due to the "Kuikae" rule
        # "Kuikae" rule: for example, chi 5s with 34s then play 2s is forbidden.
        # In this case, 2s is in operation.combination, so it should not show up in return value.
        return [cls(hand_tile, index == len(game_state.my_hand)-1 and game_state.me_just_dealt_tile)
                for index, hand_tile in enumerate(game_state.my_hand)
                if hand_tile not in operation.combination]


class Liqi(AbstractPlayTile):
    code = OperationType.LIQI

    @classmethod
    def get_possible_operations(cls, data: GameActionMessage, operation: pb.OptionalOperation,
                                game_state: GameState) -> list[Self]:
        # When operation is Liqi, operation.combination contains `almost` all possible options that allows you to riichi
        # However, see How weird operation.combination behaves:
        # 1. your hand is 0567m23p23456799s, cut 0m or 5m riichi: operation.combination only have 5m
        # 2. your hand is 0789m23p23456799s, cut 0m riichi: operation.combination only have 0m
        # So it's important to transform all 0m into 5m before comparing
        return [cls(hand_tile, index == len(game_state.my_hand)-1 and game_state.me_just_dealt_tile)
                for index, hand_tile in enumerate(game_state.my_hand)
                if hand_tile in operation.combination or hand_tile.replace('0', '5') in turn0to5(operation.combination)]


class Chi(AbstractCallOperation):
    code = OperationType.CHI


class Pong(AbstractCallOperation):
    code = OperationType.PONG


class MingGang(AbstractCallOperation):
    code = OperationType.MINGGANG


class AnGang(AbstractCallOperation):
    code = OperationType.ANGANG
    is_self_operation = True


class AddGang(AbstractCallOperation):
    code = OperationType.ADDGANG
    is_self_operation = True


class Ron(AbstractCallOperation):
    code = OperationType.RON

    @classmethod
    def get_possible_operations(cls, data: GameActionMessage, operation: pb.OptionalOperation,
                                game_state: GameState) -> list[Self]:
        retval = [cls("", [], 0), cls("", [], 0, cancel_operation=True)]
        return retval


_OPERATION_CLASS_LIST = [PlayTile, Chi, Pong, AnGang, MingGang, AddGang, Liqi, Tsumo, Ron, JiuZhongJiuPai, BaBei]
OPERATION_CLASS_DICT = {_op.code: _op for _op in _OPERATION_CLASS_LIST}

_CANCELLABLE_CLASS_LIST = [Chi, Pong, MingGang]    # TODO: Add Tsumo, AnGang (They should be cancellable after riichi)
CANCELLABLE_CLASS_DICT = {_op.code: _op for _op in _CANCELLABLE_CLASS_LIST}
