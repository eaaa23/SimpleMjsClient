from enum import IntEnum
from dataclasses import dataclass

from mjs_client.const import OperationType
from mjs_client.game.gamestate import GameState
from mjs_client.game.operation import AbstractOperation

from script_api import AbstractScript, OperationEvaluation



class BotItemMode(IntEnum):
    DETERMINE = 1
    ASK_LOWER = 2


@dataclass
class BotItem:
    script_inst: AbstractScript
    threshold: float
    mode: BotItemMode

    def decision(self, operations: dict[OperationType, list[AbstractOperation]], game_state: GameState, operation_phase: int)\
        -> list[OperationEvaluation]:
        try:
            script_evaluation = self.script_inst.decision(operations, game_state, operation_phase)
        except:
            return []
        return [evaluation for evaluation in script_evaluation if evaluation.value >= self.threshold]


class AutoBot:
    def __init__(self, name: str):
        self.name = name
        self.items: list[BotItem] = []

    def add_item(self, item: BotItem):
        self.items.append(item)

    def remove_item(self, idx: int):
        del self.items[idx]

    def set_threshold(self, idx: int, threshold: float):
        self.items[idx].threshold = threshold

    def _swap_item(self, idx_1: int, idx_2: int):
        self.items[idx_1], self.items[idx_2] = self.items[idx_2], self.items[idx_1]

    def uplift_item(self, idx: int):
        self._swap_item(idx-1, idx)

    def downgrade_item(self, idx: int):
        self._swap_item(idx, idx+1)

    def decision(self, operations: dict[OperationType, list[AbstractOperation]], game_state: GameState, operation_phase: int,
                 ) -> AbstractOperation | None:
        if not self.items:
            return None

        operations_flattened: dict[int, AbstractOperation] = {id(op): op for op_list in operations.values() for op in op_list}

        initial_candidates_evaluation_list: dict[int, float] = {}
        candidates_id: set[int] = set()
        found_initial_candidates: bool = False

        for bot_item in self.items:
            evaluations_list: list[OperationEvaluation] = bot_item.decision(operations, game_state, operation_phase)

            evaluations_id = set(id(evaluation.operation) for evaluation in evaluations_list)

            if evaluations_id:
                if found_initial_candidates:
                    intersection = candidates_id & evaluations_id
                    if intersection:
                        candidates_id = intersection

                else:
                    candidates_id = evaluations_id
                    initial_candidates_evaluation_list = {id(evaluation.operation): evaluation.value for evaluation in evaluations_list}
                    found_initial_candidates = True

        if found_initial_candidates:
            selected_id = max(candidates_id, key=lambda id_: initial_candidates_evaluation_list[id_])
            return operations_flattened[selected_id]
        else:
            return None