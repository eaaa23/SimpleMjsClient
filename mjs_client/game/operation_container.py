import logging
from typing import Generator, Iterable, Union, cast

from ..api import protocol_pb2 as pb
from ..const import OperationType

from .gamestate import GameState
from .operation import AbstractOperation, OPERATION_CLASS_DICT, PlayTile, Chi, Pong, AnGang, MingGang, AddGang, Liqi, \
    Tsumo, Ron, JiuZhongJiuPai, BaBei, CANCELLABLE_CLASS_DICT
from .phases import OperationPhase

# Only used in OperationContainer.__getitem__ to prevent static analyzer from giving warning
# Do not use this to hint anywhere else!
type AnyOperation = Union[PlayTile, Chi, Pong, AnGang, MingGang, AddGang, Liqi, Tsumo, Ron, JiuZhongJiuPai, BaBei]


class OperationContainer:
    def __init__(self):
        self._operations: dict[OperationType, list[AbstractOperation]] = {}
        self.phase: OperationPhase = OperationPhase.NO_OPERATION

    def __getitem__(self, item: OperationType) -> list[AnyOperation]:
        return cast(list[AnyOperation], self._operations.get(item, []))

    def __contains__(self, item: OperationType) -> bool:
        return item in self._operations

    def __bool__(self):
        return bool(self._operations)

    def items(self) -> Iterable[tuple[OperationType, list[AbstractOperation]]]:
        return self._operations.items()

    def flattened(self) -> Generator[AbstractOperation]:
        return (op for op_list in self._operations.values() for op in op_list)

    def clear(self):
        self._operations.clear()

    def update_from_protobuf_object(self, data, game_state: GameState):
        self._operations = {}
        if hasattr(data, "operation"):
            for op in data.operation.operation_list:
                op: pb.OptionalOperation
                possible_operations_of_type = OPERATION_CLASS_DICT[op.type].get_possible_operations(data,
                                                                                                    op,
                                                                                                    game_state)
                if possible_operations_of_type:
                    self._operations[op.type] = possible_operations_of_type

    def get_default(self) -> AbstractOperation | None:
        if self.phase == OperationPhase.NO_OPERATION:
            return None

        # Whenever possible, TSUMO and RON are always the most important. ^_^
        if tsumo := self[OperationType.TSUMO]:
            return tsumo[0]
        if ron := self[OperationType.RON]:
            return ron[0]

        # Cancellable Operations
        for code in CANCELLABLE_CLASS_DICT:
            if op_list := self[code]:
                op = op_list[-1]
                if op.cancel_operation:
                    return op_list[-1]

        # PlayTile
        if playtiles := self[OperationType.PLAY_TILE]:
            return playtiles[-1]

        # Normally this won't happen
        logging.warn("OperationContainer: get_default() found nothing, return None")
        return None

    def __str__(self):
        return '\n'.join("{}:\n".format(code) + '\n'.join(str(op) for op in op_list)
                         for code, op_list in self._operations.items())

    def __repr__(self):
        return self.__str__()
