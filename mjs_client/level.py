from typing import Self

from .const import MATCH_SID, LevelMain, CELESTIAL_MAX_SCORE, LEVEL_MAX_SCORE, MODE_INT, PlayerCount


class Level:
    """
    Usage:
        Level(*, level_id, score=0)
        Level(*, player_count, level, sublevel, score=0)

    Attributes:
        level_id: int
            5-length digital level id to communicate with the server.
        player_count: PlayerCount
            Player count, 3 or 4.
        level: LevelMain
            From NOVICE to CELESTIAL.
            See the enum const.LevelMain
        sublevel: int
            "Star" count for non-celestial level, and "Lv." for celestial.
        score: int
            "pt" for non-celestial level, and subpoint for celestial.
    """
    def __init__(self, **kwargs):
        if "level_id" in kwargs:
            self.level_id: int = kwargs["level_id"]
            self.player_count: PlayerCount = 5 - (self.level_id // 10000)   # type: ignore
            self.level: LevelMain = self.level_id // 100 % 10   # type: ignore
            self.sublevel: int = self.level_id % 10
        else:
            self.player_count: PlayerCount = kwargs["player_count"]
            self.level: LevelMain = kwargs["level"]
            self.sublevel: int = kwargs["sublevel"]
            self.level_id: int = 10000*(5-self.player_count) + 100*self.level + self.sublevel
        self.score: int = kwargs.get("score", 0)

    def match_sid(self, is_east: bool) -> int:
        return MATCH_SID[self.level][MODE_INT[self.player_count, is_east]]

    def lower(self) -> Self:
        lower_level = self.level - 2 if self.level == LevelMain.CELESTIAL else self.level - 1
        return Level(player_count=self.player_count, level=lower_level, sublevel=self.sublevel)

    def legal(self) -> bool:
        return self.level in LevelMain

    def get_match_levels(self) -> list[Self]:
        return [lv for lv in (self, self.lower()) if lv.level in MATCH_SID]

    def get_max_score(self) -> int:
        if self.level == LevelMain.CELESTIAL:
            return CELESTIAL_MAX_SCORE
        return LEVEL_MAX_SCORE[self.level][self.sublevel - 1]


def get_match_level_dict(player_count_to_level: dict[PlayerCount, Level]) -> dict[LevelMain, set[PlayerCount]]:
    """
    :player_count_to_level: dict[int(player count), level]
    :return: dict[int(available match_level), set(available player count, consists of 3 or 4)
    """
    retval: dict[LevelMain, set[PlayerCount]] = {}
    for player_count, level in player_count_to_level.items():
        match_levels = level.get_match_levels()
        for match_level in match_levels:
            retval[match_level.level] = retval.get(match_level.level, set())
            retval[match_level.level].add(player_count)
    return retval
