from dataclasses import dataclass
from enum import IntEnum
import logging

from mjs_client.game.gamestate import GameState
from mjs_client.game.operation import AbstractOperation
from mjs_client.game.operation_container import OperationContainer

from .config import AutoBotInfo
from .scripts import PackageScriptManager

from script_api import AbstractScript, Evaluation


class BotItemMode(IntEnum):
    DETERMINE = 1
    ASK_LOWER = 2


@dataclass
class BotItem:
    script_inst: AbstractScript
    threshold: float
    mode: BotItemMode = BotItemMode.DETERMINE
    faulty: bool = False

    def decision(self, operations: OperationContainer, game_state: GameState) -> list[Evaluation]:
        try:
            script_evaluation = self.script_inst.decision(operations, game_state)
            if not isinstance(script_evaluation, (list, tuple)):
                raise TypeError("not list or tuple")
            if not all(isinstance(ev, Evaluation) for ev in script_evaluation):
                raise TypeError("not Evaluation")
        except Exception as e:
            self.faulty = True
            logging.error(f"Script Evaluation Fail: {e}")
            return []
        return [evaluation for evaluation in script_evaluation if evaluation.value >= self.threshold]


class AutoBotInstantiationError(Exception):
    pass


class ScriptNotFound(AutoBotInstantiationError):
    pass


class ScriptInstanceInitFail(AutoBotInstantiationError):
    pass


class AutoBot:
    def __init__(self, scripts_manager: PackageScriptManager, autobot_info: AutoBotInfo):
        self.name = autobot_info.name

        self.items: list[BotItem] = []
        for item_info in autobot_info.items:
            script_class_wrapper = scripts_manager.find_class_from_bot_item_info(item_info)
            if script_class_wrapper is None:
                raise ScriptNotFound(item_info)

            try:
                script_inst = script_class_wrapper.script_class()
            except Exception as e:
                raise ScriptInstanceInitFail(script_class_wrapper, e)

            self.items.append(BotItem(script_inst, item_info.threshold))

    def decision(self, operations: OperationContainer, game_state: GameState) -> AbstractOperation | None:
        if not self.items:
            return None

        operations_flattened: dict[int, AbstractOperation] = {id(op): op for op in operations.flattened()}

        initial_candidates_evaluation_list: dict[int, float] = {}
        candidates_id: set[int] = set()
        found_initial_candidates: bool = False

        for bot_item in self.items:
            evaluations_list: list[Evaluation] = bot_item.decision(operations, game_state)

            evaluations_id = set(id(evaluation.operation) for evaluation in evaluations_list)

            if evaluations_id:
                if found_initial_candidates:
                    intersection = candidates_id & evaluations_id
                    if intersection:
                        candidates_id = intersection

                else:
                    candidates_id = evaluations_id
                    initial_candidates_evaluation_list = {id(evaluation.operation): evaluation.value
                                                          for evaluation in evaluations_list}
                    found_initial_candidates = True

        if found_initial_candidates:
            selected_id = max(candidates_id, key=lambda id_: initial_candidates_evaluation_list[id_])
            return operations_flattened[selected_id]
        else:
            return None
