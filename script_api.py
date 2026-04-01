from abc import ABC, abstractmethod
from dataclasses import dataclass

from mjs_client.const import OperationType
from mjs_client.game.operation import AbstractOperation
from mjs_client.game.gamestate import GameState
from mjs_client.game.action import OperationPhase


@dataclass
class OperationEvaluation:
    operation: AbstractOperation
    value: float = 0.0


class AbstractScript(ABC):
    NAME: str = ""
    NAME_LOCALIZED: dict[str, str] = {}

    def decision(self, operations: dict[OperationType, list[AbstractOperation]], game_state: GameState, operation_phase: int)\
            -> list[OperationEvaluation]:
        match operation_phase:
            case OperationPhase.SELF_TURN:
                return self.self_turn(operations, game_state)
            case OperationPhase.AFTER_SELF_CPG:
                return self.after_self_called(operations, game_state)
            case OperationPhase.OTHER_PLAYED:
                return self.other_played(operations, game_state)
            case OperationPhase.AFTER_OTHER_ZIMING:
                return self.other_call_in_turn(operations, game_state)
            case _:
                return []

    @abstractmethod
    def self_turn(self, operations: dict[OperationType, list[AbstractOperation]], game_state: GameState):
        raise NotImplementedError

    @abstractmethod
    def after_self_called(self, operations: dict[OperationType, list[AbstractOperation]], game_state: GameState):
        raise NotImplementedError

    @abstractmethod
    def other_played(self, operations: dict[OperationType, list[AbstractOperation]], game_state: GameState):
        raise NotImplementedError

    @abstractmethod
    def other_call_in_turn(self, operations: dict[OperationType, list[AbstractOperation]], game_state: GameState):
        raise NotImplementedError



