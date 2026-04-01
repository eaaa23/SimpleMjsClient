import asyncio
from enum import IntEnum
from sortedcontainers import SortedList

from .gamephase import GamePhase
from .tiles_util import tile_cmp_key, turn0to5
from ..api import protocol_pb2 as pb
from .gamestate import GameState, Discard, Open, OpenType, OpenDirection, RoundResult, WinInfo, EndResult
from .operation import OperationType, OPERATION_CLASS_DICT, AbstractOperation
from ..const import AnGangAddGangType, CPGType
from ..exceptions import GameError


class OperationPhase(IntEnum):
    DEFAULT = -1
    SELF_TURN = 0
    OTHER_PLAYED = 1
    AFTER_SELF_CPG = 2
    AFTER_OTHER_ZIMING = 3


class AbstractGameAction:
    data_class: type(object)
    operation_delay: float = 0.0
    def __init__(self, step, data):
        self.step = step
        self.data = data

    def __lt__(self, other):
        return self.step < other.step

    def update(self, game_state: GameState) -> int:
        return OperationPhase.DEFAULT

class GameActionWithLiqiSuccess(AbstractGameAction):
    def update_liqi(self, game_state: GameState):
        liqi = self.data.liqi
        if liqi.liqibang and not liqi.failed:
            game_state.liqibang = liqi.liqibang
            game_state.scores[liqi.seat] = liqi.score

class PlaceHolder(AbstractGameAction):
    pass

class ActionMJStart(AbstractGameAction):
    data_class = pb.ActionMJStart

class ActionNewRound(AbstractGameAction):
    data_class = pb.ActionNewRound
    operation_delay = 3.0
    def update(self, game_state: GameState) -> int:
        game_state.current_chang, game_state.current_ju, game_state.current_benchang = self.data.chang, self.data.ju, self.data.ben
        game_state.my_hand = sorted(self.data.tiles, key=tile_cmp_key)
        game_state.doras = list(self.data.doras)
        for i, score in enumerate(self.data.scores):
            game_state.scores[i] = score
        game_state.liqibang = self.data.liqibang
        game_state.left_tile_count = self.data.left_tile_count
        game_state.me_just_dealt_tile = len(game_state.my_hand) == 14
        for seat in range(game_state.player_count):
            game_state.player_hand_size[seat] = (14 if seat == game_state.current_ju else 13)
        game_state.reset_player_info()
        return OperationPhase.SELF_TURN if game_state.me_just_dealt_tile else OperationPhase.DEFAULT


class ActionDealTile(GameActionWithLiqiSuccess):
    data_class = pb.ActionDealTile
    def update(self, game_state: GameState) -> int:
        self.update_liqi(game_state)
        game_state.player_hand_size[self.data.seat] += 1
        game_state.last_operation_is_deal = True
        is_my_deal = self.data.tile and game_state.my_seat == self.data.seat
        is_deal_after_angang = bool(self.data.doras)
        if not is_my_deal and not is_deal_after_angang:
            game_state.left_tile_count -= 1
            return OperationPhase.DEFAULT
        game_state.left_tile_count = self.data.left_tile_count
        if is_my_deal:
            game_state.my_hand.append(self.data.tile)
            game_state.me_just_dealt_tile = True
        if is_deal_after_angang:
            game_state.doras = list(self.data.doras)
        return OperationPhase.SELF_TURN


class ActionDiscardTile(AbstractGameAction):
    data_class = pb.ActionDiscardTile
    def update(self, game_state: GameState) -> int:
        game_state.last_discard = Discard(tile=self.data.tile, moqie=self.data.moqie,
                                                                  called=False, is_liqi=(self.data.is_liqi or self.data.is_wliqi))
        game_state.player_discards[self.data.seat].append(game_state.last_discard)
        game_state.player_hand_size[self.data.seat] -= 1
        if self.data.is_wliqi:
            game_state.player_liqis[self.data.seat] = 2
        elif self.data.is_liqi:
            game_state.player_liqis[self.data.seat] = 1
        if self.data.doras:
            game_state.doras = list(self.data.doras)
        if self.data.seat == game_state.my_seat:
            game_state.my_hand.remove(self.data.tile)
            game_state.my_hand.sort(key=tile_cmp_key)
            game_state.me_just_dealt_tile = False
        return OperationPhase.OTHER_PLAYED


class ActionChiPengGang(GameActionWithLiqiSuccess):
    data_class = pb.ActionChiPengGang
    def update(self, game_state: GameState) -> int:
        for i, from_ in enumerate(self.data.froms):
            if from_ != self.data.seat:
                direction = (from_ - self.data.seat) % 4
                break
        else:
            raise GameError(-1, "ChiPengGang all from data.seat")
        tiles = list(self.data.tiles)
        tile_from_other = tiles[i]
        del tiles[i]
        game_state.player_opens[self.data.seat].append(Open(type=self.data.type, tiles_self=tiles, direction=direction, tile_from_other=tile_from_other))
        game_state.player_hand_size[self.data.seat] -= (3 if self.data.type == CPGType.MINGGANG else 2)
        game_state.last_discard.called = True
        if self.data.seat == game_state.my_seat:
            for tile in tiles:
                game_state.my_hand.remove(tile)
        self.update_liqi(game_state)
        return OperationPhase.AFTER_SELF_CPG


class ActionAnGangAddGang(AbstractGameAction):
    data_class = pb.ActionAnGangAddGang
    def update(self, game_state: GameState) -> int:
        if self.data.type == AnGangAddGangType.ANGANG:
            if self.data.tiles[0] in ('0', '5'):
                tile_0 = '0' + self.data.tiles[1]
                tile_5 = '5' + self.data.tiles[1]
                tiles_self = [tile_5, tile_5, tile_0, tile_5]
            else:
                tiles_self = [self.data.tiles] * 4
            game_state.player_opens[self.data.seat].append(
                Open(type=OpenType.ANGANG, tiles_self=tiles_self))
            game_state.player_hand_size[self.data.seat] -= 4
            if self.data.seat == game_state.my_seat:
                for tile in tiles_self:
                    game_state.my_hand.remove(tile)
        elif self.data.type == AnGangAddGangType.ADDGANG:
            game_state.player_hand_size[self.data.seat] -= 1
            for open_ in game_state.player_opens[self.data.seat]:
                if open_.type == OpenType.PONG and open_.tile_from_other.replace('0', '5') == self.data.tiles.replace('0', '5'):
                    open_.type = OpenType.ADDGANG
                    open_.tiles_self.append(self.data.tiles)
                    if self.data.seat == game_state.my_seat:
                        game_state.my_hand.remove(self.data.tiles)
                    break
            else:
                #logging.warn(f"AddGang cannot find corresponding PONG-fulu")
                pass
        return OperationPhase.AFTER_OTHER_ZIMING


class ActionBaBei(AbstractGameAction):
    data_class = pb.ActionBaBei
    def update(self, game_state: GameState) -> int:
        game_state.player_peis[self.data.seat].append(self.data.moqie)
        game_state.player_hand_size[self.data.seat] -= 1
        if game_state.me_just_dealt_tile:
            if self.data.moqie:
                del game_state.my_hand[-1]
            else:
                game_state.my_hand.remove('4z')
            return OperationPhase.SELF_TURN
        return OperationPhase.AFTER_OTHER_ZIMING


class RoundEnder(AbstractGameAction):
    def result(self, game_state: GameState) -> RoundResult:
        pass


class ActionHule(RoundEnder):
    data_class = pb.ActionHule
    def result(self, game_state: GameState) -> RoundResult:
        return RoundResult(shown_hands={hule.seat: (list(hule.hand) + [hule.hu_tile], game_state.player_opens[hule.seat]) for hule in self.data.hules},
                           delta_scores=list(self.data.delta_scores),
                           win=[WinInfo(seat=hule.seat,
                                        yakus={fan.id: fan.val for fan in hule.fans},
                                        fan=hule.count,
                                        fu=hule.fu,
                                        score=hule.dadian,
                                        tsumo=hule.zimo,
                                        yakuman=hule.yiman) for hule in self.data.hules])


class ActionLiuJu(RoundEnder):
    data_class = pb.ActionLiuJu
    def result(self, game_state: GameState) -> RoundResult:
        return RoundResult(shown_hands={}, delta_scores=[0 for i in range(game_state.player_count)], win=[])


class ActionNoTile(RoundEnder):
    data_class = pb.ActionNoTile
    def result(self, game_state: GameState) -> RoundResult:
        shown_hands = {i: (player.hand, game_state.player_opens[i]) for i, player in enumerate(self.data.players) if player.tingpai}
        if self.data.scores:
            delta_scores = list(self.data.scores[0].delta_scores)
            delta_scores.extend([0] * (game_state.player_count - len(delta_scores)))
        else:
            delta_scores = [0 for i in range(game_state.player_count)]
        return RoundResult(shown_hands=shown_hands, delta_scores=delta_scores, win=[])



NAME_DICT = {"ActionNewRound": ActionNewRound, "ActionMJStart": ActionMJStart, "ActionDealTile": ActionDealTile,
             "ActionDiscardTile": ActionDiscardTile, "ActionChiPengGang": ActionChiPengGang,
             "ActionAnGangAddGang": ActionAnGangAddGang, "ActionBaBei": ActionBaBei, "ActionHule": ActionHule,
             "ActionLiuJu": ActionLiuJu, "ActionNoTile": ActionNoTile}


class GameActionHandler:
    def __init__(self, game, player_count: int, is_east: bool, my_seat: int):
        self.game = game
        self.action_queue = SortedList()
        self.game_state = GameState(player_count, is_east, my_seat)
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
                raise ValueError(f"GameActionQueue Failure: GameActionHandler ptr at {self.next_step}, received action step={this_action.step}")
            elif self.next_step == this_action.step:
                if isinstance(this_action, RoundEnder):
                    self.game_state.round_result = this_action.result(self.game_state)
                    self.game_state.phase = GamePhase.BETWEEN_ROUNDS
                    self.clear_actions()
                    self.game_state.possible_operations = {}
                    self.game.client.update_event.set()
                    return
                self.game_state.last_operation_is_deal = False
                self.game_state.phase = GamePhase.IN_PROGRESS
                operation_phase = this_action.update(self.game_state)
                self.game_state.possible_operations = self.get_possible_operations(this_action.data)
                self.action_queue.pop(0)
                self.next_step += 1
                self.game.client.update_event.set()
                #logging.info(f"ActionHandler updated step from {this_action.step} to {self.next_step}")
            else:
                #logging.info(f"ActionHandler blocking, now ptr at {self.next_step}, this_action at {this_action.step}")
                break
        #logging.info(f"Debug-gamestate: my_hand={self.game_state.my_hand}")

    def get_possible_operations(self, data) -> dict[OperationType, list[AbstractOperation]]:
        retval = {}
        if hasattr(data, "operation"):
            for op in data.operation.operation_list:
                possible_operations_of_type = OPERATION_CLASS_DICT[op.type].get_possible_operations(data, op, self.game_state)
                if possible_operations_of_type:
                    retval[op.type] = possible_operations_of_type
        return retval

    def end_game(self, result_protobuf):
        self.clear_actions()
        self.game_state.game_result = [EndResult(seat=player_item.seat,
                                                 point=player_item.part_point_1,
                                                 score=player_item.total_point / 1000,
                                                 pt=player_item.grading_score)
                                       for player_item in result_protobuf.players]
        self.game_state.ended = True
