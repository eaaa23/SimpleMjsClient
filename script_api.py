from abc import ABC, abstractmethod
from dataclasses import dataclass

from mjs_client.game.gamestate import GameState
from mjs_client.game.operation import AbstractOperation
from mjs_client.game.operation_container import OperationContainer
from mjs_client.game.phases import OperationPhase


@dataclass
class Evaluation:
    operation: AbstractOperation
    value: float


class AbstractScript(ABC):
    NAME: str = ""
    NAME_LOCALIZED: dict[str, str] = {}

    def decision(self, operations: OperationContainer, game_state: GameState) -> list[Evaluation]:
        match operations.phase:
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
    def self_turn(self, operations: OperationContainer, game_state: GameState) -> list[Evaluation]:
        raise NotImplementedError

    @abstractmethod
    def after_self_called(self, operations: OperationContainer, game_state: GameState) -> list[Evaluation]:
        raise NotImplementedError

    @abstractmethod
    def other_played(self, operations: OperationContainer, game_state: GameState) -> list[Evaluation]:
        raise NotImplementedError

    @abstractmethod
    def other_call_in_turn(self, operations: OperationContainer, game_state: GameState) -> list[Evaluation]:
        raise NotImplementedError
