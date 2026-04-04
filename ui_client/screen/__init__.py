from .abstract import AbstractScreen
from .blank import BlankScreen
from .login import LoginScreen
from .lobby import LobbyScreen
from .room import RoomScreen
from .game import GameScreen


_MAIN_SCREENS = [BlankScreen, LoginScreen, LobbyScreen, RoomScreen, GameScreen]
MAIN_SCREENS = {scr_type.PHASE: scr_type for scr_type in _MAIN_SCREENS}
