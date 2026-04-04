import logging

from mjs_client.const import OperationType
from mjs_client.game.gamestate import GameState
from mjs_client.game.operation import AbstractOperation, AbstractPlayTile, PlayTile
from mjs_client.game.operation_container import OperationContainer
from script_api import AbstractScript, Evaluation


def is_yaochu(tile: str) -> bool:
    return tile.endswith("z") or tile.startswith("1") or tile.startswith("9")


class KokushiScript(AbstractScript):
    def self_turn(self, operations: OperationContainer, game_state: GameState) -> list[Evaluation]:
        if OperationType.TSUMO in operations:
            return [Evaluation(operations[OperationType.TSUMO][0], 1.0)]

        playtiles: list[PlayTile] = operations[OperationType.PLAY_TILE]
        non_yaochus: list[PlayTile] = list(filter(lambda op: not is_yaochu(op.tile), playtiles))
        if non_yaochus:
            return [Evaluation(op, 1.0) for op in non_yaochus]

        repeated = list(filter(lambda op: game_state.my_hand.count(op.tile) >= 2, playtiles))
        if repeated:
            return [Evaluation(op, 1.0) for op in repeated]
        else:
            logging.error(f"TestScript: What the heck? All yaochu tiles without a pair")
            return []

    def other_call_in_turn(self, operations: OperationContainer, game_state: GameState):
        return []

    def after_self_called(self, operations: OperationContainer, game_state: GameState):
        return []

    def other_played(self, operations: OperationContainer, game_state: GameState):
        return []

    NAME: str = "Kokushi (13 Orphans) Beta"

    NAME_LOCALIZED = {"CN": "国士无双 测试版"}

