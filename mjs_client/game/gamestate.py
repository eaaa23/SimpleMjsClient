from enum import IntEnum
from dataclasses import dataclass

from .gamephase import GamePhase
from .tiles_util import tile_cmp_key, TILES_TO_INDEX34, SANMA_INVALID_TILES



class OpenType(IntEnum):
    """
    These values are not fully for client-server communication.
    Though CHI, PONG, MINGGANG matches CPGType in ..const.py,
    ANGANG, ADDGANG has nothing to do with the client-server communication codes.
    """
    CHI = 0
    PONG = 1
    MINGGANG = 2
    ANGANG = 3
    ADDGANG = 4

class OpenDirection(IntEnum):
    NONE = 0
    NEXT = 1
    LAST = 3
    OPPOSE = 2


@dataclass
class Open:
    type: int
    tiles_self: list[str]
    direction: int = OpenDirection.NONE
    tile_from_other: str = ""


@dataclass
class Discard:
    tile: str
    moqie: bool
    called: bool
    is_liqi: bool


@dataclass
class EndResult:
    seat: int = 0
    point: int = 0
    score: float = 0.0
    pt: int = 0



class GameState:
    def __init__(self, player_count: int, is_east: bool, my_seat: int):
        self.player_count = player_count
        self.is_east = is_east
        self.my_seat: int = my_seat
        self.current_chang: int = 0
        self.current_ju: int = 0
        self.current_benchang: int = 0
        #self.whose_turn = 0
        self.doras: list[str] = []
        self.scores: list[int] = [0]*4
        self.liqibang: int = 0
        self.left_tile_count: int = 0
        self.my_hand: list[str] = []
        self.me_just_dealt_tile: bool = False
        self.last_operation_is_deal: bool = False
        self.last_discard: Discard = None
        self.phase: int = GamePhase.EMPTY
        self.player_hand_size: list[int] = [0 for i in range(4)]
        self.player_discards: list[list[Discard]] = [[] for i in range(4)]
        self.player_opens: list[list[Open]] = [[] for i in range(4)]
        self.player_peis: list[list[bool]] = [[] for i in range(4)]
        self.player_liqis: list[int] = [0]*4
        self.round_result: RoundResult = RoundResult({}, [], [])

        self.ended: bool = False
        # The only list index by rank, not by seat.
        self.game_result: list[EndResult] = []

        self.possible_operations: dict[int, list] = {}
        self._all_visible_tiles34: list[int] = [0]*34

    def reset_player_info(self):
        self.player_discards: list[list[Discard]] = [[] for i in range(4)]
        self.player_opens: list[list[Open]] = [[] for i in range(4)]
        self.player_peis: list[list[bool]] = [[] for i in range(4)]
        self.player_liqis = [0] * 4

    """
    def __str__(self):
        retval = f"\nCurrent chang={self.current_chang}, ju={self.current_ju}, ben={self.current_benchang}\n\n"
        for i in range(self.player_count):
            retval += f"seat {i}{' (me)' if i == self.my_seat else ''}, liqistate={self.player_liqis[i]}, score={self.scores[i]}\n" \
                      f"Shepai: {''.join(shepai.tile for shepai in self.player_discards[i])}\n" \
                      f"Fulu: {' '.join(fulu.to_string(i) for fulu in self.player_opens[i])}    BaBei: {len(self.player_peis[i])}\n"
            if i == self.my_seat:
                retval += f'Original hand: {''.join(self.my_hand)}\n'
                retval += ''.join(sorted(self.my_hand, key=tile_cmp_key)) + "\n"
            retval += "\n"
        return retval
        """

class RoundResultType(IntEnum):
    HULE = 0
    LIUJU = 1


@dataclass
class WinInfo:
    seat: int
    yakus: dict[int, int]
    fan: int
    fu: int
    score: int
    tsumo: bool
    yakuman: bool = False



@dataclass
class RoundResult:
    shown_hands: dict[int, tuple[list[str], list[Open]]]
    delta_scores: list[int]
    win: list[WinInfo]

