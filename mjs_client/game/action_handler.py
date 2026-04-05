import asyncio
import logging

from sortedcontainers import SortedList

from .action import AbstractGameAction, RoundEnder
from .gamestate import GameState, EndResult
from .operation_container import OperationContainer
from .phases import GamePhase


class GameActionHandler:
    def __init__(self, game, player_count: int, is_east: bool, my_seat: int):
        self.game = game
        self.action_queue = SortedList()
        self.game_state: GameState = GameState(player_count, is_east, my_seat)
        self.possible_operations = OperationContainer()
        self.next_step = 0
        self.lock = asyncio.Event()
        self.lock.set()

    def add_action(self, action: AbstractGameAction):
        self.action_queue.add(action)

    def clear_actions(self):
        self.action_queue.clear()
        self.next_step = 0

    async def update(self):
        await self.lock.wait()
        for i in range(len(self.action_queue)):
            this_action: AbstractGameAction = self.action_queue[0]
            if self.next_step > this_action.step:
                raise ValueError(f"GameActionQueue Failure: GameActionHandler ptr at {self.next_step}, "
                                 f"received action step={this_action.step}")
            elif self.next_step == this_action.step:
                if isinstance(this_action, RoundEnder):
                    self.game_state.round_result = this_action.result(self.game_state)
                    self.game_state.phase = GamePhase.BETWEEN_ROUNDS
                    self.clear_actions()
                    self.possible_operations.clear()
                    self.game.client.update_event.set()
                    return

                self.game_state.last_operation_is_deal = False
                self.game_state.phase = GamePhase.IN_PROGRESS

                self.possible_operations.phase = this_action.update(self.game_state)
                self.possible_operations.update_from_protobuf_object(this_action.data, self.game_state)

                self.action_queue.pop(0)
                self.next_step += 1
                self.game.client.update_event.set()
                # logging.info(f"ActionHandler updated step from {this_action.step} to {self.next_step}")
            else:
                logging.warn(f"ActionHandler blocking, now ptr at {self.next_step}, this_action at {this_action.step}")
                break

    def end_game(self, result_protobuf):
        self.clear_actions()
        self.game_state.game_result = [EndResult(seat=player_item.seat,
                                                 point=player_item.part_point_1,
                                                 score=player_item.total_point / 1000,
                                                 pt=player_item.grading_score)
                                       for player_item in result_protobuf.players]
        self.game_state.ended = True
