from mjs_client.game.gamestate import GameState
from mjs_client.game.operation import AbstractOperation
from script_api import AbstractScript


class TestScript2(AbstractScript):
    def other_played(self, operations: dict[int, list[AbstractOperation]], game_state: GameState):
        pass

    def other_call_in_turn(self, operations: dict[int, list[AbstractOperation]], game_state: GameState):
        pass

    def after_self_called(self, operations: dict[int, list[AbstractOperation]], game_state: GameState):
        pass

    def self_turn(self, operations: dict[int, list[AbstractOperation]], game_state: GameState):
        pass

    NAME: str = "Test 2"



