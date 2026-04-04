from typing import Generator, Iterable

from ..const import OperationType

from .gamestate import GameState
from .operation import AbstractOperation, OPERATION_CLASS_DICT
from .phases import OperationPhase



class OperationContainer:
    def __init__(self):
        self._operations: dict[OperationType, list[AbstractOperation]] = {}
        self.phase: OperationPhase = OperationPhase.NO_OPERATION

    def __getitem__(self, item: OperationType) -> list[AbstractOperation]:
        return self._operations.get(item, [])

    def __contains__(self, item: OperationType) -> bool:
        return item in self._operations

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
                possible_operations_of_type = OPERATION_CLASS_DICT[op.type].get_possible_operations(data, op, game_state)
                if possible_operations_of_type:
                    self._operations[op.type] = possible_operations_of_type

    def __str__(self):
        return '\n'.join("{}:\n".format(code) + '\n'.join(str(op) for op in op_list) for code, op_list in self._operations.items())

    def __repr__(self):
        return self.__str__()

