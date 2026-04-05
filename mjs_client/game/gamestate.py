from dataclasses import dataclass, field
from enum import IntEnum

from .phases import GamePhase


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
    shown_hands: dict[int, tuple[list[str], list[Open]]] = field(default_factory=dict)
    delta_scores: list[int] = field(default_factory=lambda: [0 for i in range(4)])
    win: list[WinInfo] = field(default_factory=list)


@dataclass
class GameState:
    player_count: int
    is_east: bool
    my_seat: int
    current_chang: int = 0
    current_ju: int = 0
    current_benchang: int = 0
    doras: list[str] = field(default_factory=list)
    scores: list[int] = field(default_factory=lambda: [0 for i in range(4)])
    liqibang: int = 0
    left_tile_count: int = 0
    my_hand: list[str] = field(default_factory=list)
    me_just_dealt_tile: bool = False
    last_operation_is_deal: bool = False
    last_discard: Discard | None = None
    phase: GamePhase = GamePhase.EMPTY
    player_hand_size: list[int] = field(default_factory=lambda: [0 for i in range(4)])
    player_discards: list[list[Discard]] = field(default_factory=lambda: [[] for i in range(4)])
    player_opens: list[list[Open]] = field(default_factory=lambda: [[] for i in range(4)])
    player_peis: list[list[bool]] = field(default_factory=lambda: [[] for i in range(4)])
    player_liqis: list[int] = field(default_factory=lambda: [0 for i in range(4)])
    round_result: RoundResult = field(default_factory=RoundResult)

    ended: bool = False
    # The only list index by rank, not by seat.
    game_result: list[EndResult] = field(default_factory=list)

    def reset_player_info(self):
        self.player_discards: list[list[Discard]] = [[] for i in range(4)]
        self.player_opens: list[list[Open]] = [[] for i in range(4)]
        self.player_peis: list[list[bool]] = [[] for i in range(4)]
        self.player_liqis = [0] * 4
