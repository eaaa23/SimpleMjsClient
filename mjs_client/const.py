from enum import IntEnum

MS_HOST = "https://game.maj-soul.com"
ENDPOINT = "wss://route-{}.maj-soul.com/"


"""
Following enum values are constants used to communicate with the server.
"""


class OperationType(IntEnum):
    PLAY_TILE = 1
    CHI = 2
    PONG = 3
    ANGANG = 4
    MINGGANG = 5
    ADDGANG = 6
    LIQI = 7
    TSUMO = 8
    RON = 9
    JIUZHONGJIUPAI = 10
    BABEI = 11


class CPGType(IntEnum):
    CHI = 0
    PONG = 1
    MINGGANG = 2


class AnGangAddGangType(IntEnum):
    ADDGANG = 2
    ANGANG = 3


class ModeInt(IntEnum):
    """
    Used in room creating
    """
    MODE_4E = 1
    MODE_4S = 2
    MODE_3E = 11
    MODE_3S = 12


# key: (player, is_east)
MODE_INT = {(4, True): ModeInt.MODE_4E,
            (4, False): ModeInt.MODE_4S,
            (3, True): ModeInt.MODE_3E,
            (3, False): ModeInt.MODE_3S}


class MatchSid(IntEnum):
    BRONZE_4E = 2
    BRONZE_4S = 3
    SILVER_4E = 5
    SILVER_4S = 6
    GOLD_4E = 8
    GOLD_4S = 9
    JADE_4E = 11
    JADE_4S = 12
    THRONE_4E = 15
    THRONE_4S = 16
    BRONZE_3E = 17
    BRONZE_3S = 18
    SILVER_3E = 19
    SILVER_3S = 20
    GOLD_3E = 21
    GOLD_3S = 22
    JADE_3E = 23
    JADE_3S = 24
    THRONE_3E = 25
    THRONE_3S = 26


class LevelMain(IntEnum):
    # Part of the level_id to communicate with server
    NOVICE = 1
    ADEPT = 2
    EXPERT = 3
    MASTER = 4
    SAINT = 5
    CELESTIAL = 7


# key: (level_m, mode_int, is_east)
MATCH_SID: dict[int, dict[int, int]] = {
    LevelMain.NOVICE: {
        ModeInt.MODE_4E: MatchSid.BRONZE_4E,
        ModeInt.MODE_4S: MatchSid.BRONZE_4S,
        ModeInt.MODE_3E: MatchSid.BRONZE_3E,
        ModeInt.MODE_3S: MatchSid.BRONZE_3S,
    },
    LevelMain.ADEPT: {
        ModeInt.MODE_4E: MatchSid.SILVER_4E,
        ModeInt.MODE_4S: MatchSid.SILVER_4S,
        ModeInt.MODE_3E: MatchSid.SILVER_3E,
        ModeInt.MODE_3S: MatchSid.SILVER_3S,
    },
    LevelMain.EXPERT: {
        ModeInt.MODE_4E: MatchSid.GOLD_4E,
        ModeInt.MODE_4S: MatchSid.GOLD_4S,
        ModeInt.MODE_3E: MatchSid.GOLD_3E,
        ModeInt.MODE_3S: MatchSid.GOLD_3S,
    },
    LevelMain.MASTER: {
        ModeInt.MODE_4E: MatchSid.JADE_4E,
        ModeInt.MODE_4S: MatchSid.JADE_4S,
        ModeInt.MODE_3E: MatchSid.JADE_3E,
        ModeInt.MODE_3S: MatchSid.JADE_3S,
    },
    LevelMain.SAINT: {
        ModeInt.MODE_4E: MatchSid.THRONE_4E,
        ModeInt.MODE_4S: MatchSid.THRONE_4S,
        ModeInt.MODE_3E: MatchSid.THRONE_3E,
        ModeInt.MODE_3S: MatchSid.THRONE_3S,
    }
}


LEVEL_MAX_SCORE: dict[int, tuple[int, ...]] = {
    LevelMain.NOVICE: (20, 80, 200),
    LevelMain.ADEPT: (600, 800, 1000),
    LevelMain.EXPERT: (1200, 1400, 2000),
    LevelMain.MASTER: (2800, 3200, 3600),
    LevelMain.SAINT: (4000, 6000, 9000)
}
CELESTIAL_MAX_SCORE = 20

TIME_FIXED_ADD: list[tuple[int, int]] = [
    (3, 5),
    (5, 10),
    (5, 20),
    (60, 0),
    (300, 0)
]
