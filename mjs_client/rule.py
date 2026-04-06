from dataclasses import dataclass, fields

from .const import ModeInt, PlayerCount


@dataclass
class DetailRule:
    init_point: int
    fandian: int
    dora_count: int
    time_fixed: int = 5
    time_add: int = 20
    shiduan: bool = True
    can_jifei: bool = True
    bianjietishi: bool = True
    ai_level: int = 1
    fanfu: int = 1

    @classmethod
    def from_protobuf(cls, buf):
        return DetailRule(**{field.name: getattr(buf, field.name) for field in fields(DetailRule)})


def get_default_rule(player_count: PlayerCount) -> DetailRule:
    if player_count == 4:
        return DetailRule(init_point=25000, fandian=30000, dora_count=3)
    elif player_count == 3:
        return DetailRule(init_point=35000, fandian=40000, dora_count=2)
    raise ValueError("player_count must be 3 or 4")


def get_mode_int(player_count: PlayerCount, is_east: bool) -> int:
    if player_count == 4:
        return ModeInt.MODE_4E if is_east else ModeInt.MODE_4S
    elif player_count == 3:
        return ModeInt.MODE_3E if is_east else ModeInt.MODE_3S
    raise ValueError("player_count must be 3 or 4")


def mode_int_is_east(mode_int: int) -> bool:
    return mode_int in (ModeInt.MODE_3E, ModeInt.MODE_4E)


def is_valid_point(point: int) -> bool:
    return point % 100 == 0 and 0 <= point <= 200000
