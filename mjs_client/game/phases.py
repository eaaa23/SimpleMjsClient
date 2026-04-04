from enum import IntEnum


class GamePhase(IntEnum):
    EMPTY = -1
    STARTING = 0
    IN_PROGRESS = 1
    BETWEEN_ROUNDS = 2
    ENDED = 3


class OperationPhase(IntEnum):
    NO_OPERATION = -1
    SELF_TURN = 0
    OTHER_PLAYED = 1
    AFTER_SELF_CPG = 2
    AFTER_OTHER_ZIMING = 3
