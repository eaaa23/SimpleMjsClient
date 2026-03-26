from typing import Self

from .const import MATCH_SID, LevelMain, CELESTIAL_MAX_SCORE, LEVEL_MAX_SCORE, MODE_INT


class Level:
    def __init__(self, **kwargs):
        if "level_id" in kwargs:
            self.level_id = kwargs["level_id"]
            self.player_count = 5 - (self.level_id // 10000)
            self.level = self.level_id // 100 % 10
            self.sublevel = self.level_id % 10
        else:
            self.player_count = kwargs["player_count"]
            self.level = kwargs["level"]
            self.sublevel = kwargs["sublevel"]
            self.level_id = 10000*(5-self.player_count) + 100*self.level + self.sublevel
        self.score = kwargs.get("score", 0)

    def match_sid(self, is_east: bool) -> int:
        return MATCH_SID[self.level][MODE_INT[self.player_count, is_east]]

    def lower(self) -> Self:
        lower_level = self.level - 2 if self.level == LevelMain.CELESTIAL else self.level - 1
        return Level(player_count=self.player_count, level=lower_level, sublevel=self.sublevel)

    def legal(self) -> bool:
        return self.level in LevelMain

    def get_match_levels(self) -> list[Self]:
        return [l for l in (self, self.lower()) if l.level in MATCH_SID]

    def get_max_score(self) -> int:
        if self.level == LevelMain.CELESTIAL:
            return CELESTIAL_MAX_SCORE
        return LEVEL_MAX_SCORE[self.level][self.sublevel - 1]



def get_match_level_dict(player_count_to_level: dict[int, Level]) -> dict[int, set[int]]:
    """
    :player_count_to_level: dict[int(player count), level]
    :return: dict[int(available match_level), set(available player count, consists of 3 or 4)
    """
    retval: dict[int, set[int]] = {}
    for player_count, level in player_count_to_level.items():
        match_levels = level.get_match_levels()
        for match_level in match_levels:
            retval[match_level.level] = retval.get(match_level.level, set())
            retval[match_level.level].add(player_count)
    return retval
