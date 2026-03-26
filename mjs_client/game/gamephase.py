from enum import IntEnum


class GamePhase(IntEnum):
    EMPTY = -1
    STARTING = 0
    IN_PROGRESS = 1
    BETWEEN_ROUNDS = 2
    ENDED = 3