import tkinter as tk
from functools import partial

from mjs_client.client import ClientPhase
from mjs_client.const import ModeInt
from mjs_client.level import get_match_level_dict

from ...language import tr
from ..settings.button import SettingsButton

from ..abstract import AbstractScreen

from .create_room import CreateRoomScreen
from .join_room import JoinRoomScreen


class LobbyLevelFrame:
    """
    This is not a screen, only a frame in LobbyScreen
    """
    def __init__(self, parent, ui, match_level: int, available_player_count: set[int]):
        self.parent = parent
        self.ui = ui
        self.match_level = match_level

        self.label_level = tk.Label(parent)
        self.label_level.grid(row=0, column=0)

        self.frame_buttons = tk.Frame(parent)
        self.frame_buttons.grid(row=0, column=1)

        self.button_4E = tk.Button(self.frame_buttons, command=partial(self.start_match, 4, True))
        self.button_4E.grid(row=0, column=0)

        self.button_4S = tk.Button(self.frame_buttons, command=partial(self.start_match, 4, False))
        self.button_4S.grid(row=0, column=1)

        if 4 not in available_player_count:
            self.button_4E.config(state=tk.DISABLED)
            self.button_4S.config(state=tk.DISABLED)

        self.button_3E = tk.Button(self.frame_buttons, command=partial(self.start_match, 3, True))
        self.button_3E.grid(row=1, column=0)

        self.button_3S = tk.Button(self.frame_buttons, command=partial(self.start_match, 3, False))
        self.button_3S.grid(row=1, column=1)

        if 3 not in available_player_count:
            self.button_3E.config(state=tk.DISABLED)
            self.button_3S.config(state=tk.DISABLED)

    def start_match(self, player: int, is_east: bool):
        self.ui.controller.start_unified_match(self.match_level, player, is_east)

    def update_text(self):
        self.label_level.config(text=tr("game.room_level.{}".format(self.match_level)))
        self.button_4E.config(text=tr("game.mode.{}".format(ModeInt.MODE_4E)))
        self.button_4S.config(text=tr("game.mode.{}".format(ModeInt.MODE_4S)))
        self.button_3E.config(text=tr("game.mode.{}".format(ModeInt.MODE_3E)))
        self.button_3S.config(text=tr("game.mode.{}".format(ModeInt.MODE_3S)))



class LobbyScreen(AbstractScreen):
    PHASE = ClientPhase.LOBBY
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.account_info_frame = tk.Frame(self.frame)
        self.account_info_frame.grid(row=0, column=0)

        self.account_info_4 = tk.Label(self.account_info_frame)
        self.account_info_4.grid(row=0, column=0)

        self.account_info_3 = tk.Label(self.account_info_frame)
        self.account_info_3.grid(row=1, column=0)

        self.subframes: list[LobbyLevelFrame] = []
        row = 1
        for match_level, available_player_count in \
                get_match_level_dict({3: self.client.account_level[3], 4: self.client.account_level[4]}).items():
            new_frame = tk.Frame(self.frame)
            new_frame.grid(row=row, column=0)
            row += 1
            self.subframes.append(LobbyLevelFrame(new_frame, ui, match_level, available_player_count))

        self.room_frame = tk.Frame(self.frame)
        self.room_frame.grid(row=row, column=0)

        self.label_room = tk.Label(self.room_frame)
        self.label_room.grid(row=0, column=0)

        self.button_create_room = tk.Button(self.room_frame, command=partial(self.new_window, CreateRoomScreen))
        self.button_create_room.grid(row=0, column=1)

        self.button_join_room = tk.Button(self.room_frame, command=partial(self.new_window, JoinRoomScreen))
        self.button_join_room.grid(row=0, column=2)

        self.settings_button = SettingsButton(self.frame, self)
        self.settings_button.grid(row=row+1, column=3)

        self.update_text()

    def get_account_info_text(self, player_count: int) -> str:
        level = self.client.account_level[player_count]
        return (tr("game.player_count.{}".format(player_count)) +
                tr("game.level.{}".format(level.level)) +
                "{}    {}/{}".format(level.sublevel, level.score, level.get_max_score()))


    def update_text(self):
        self.account_info_4.config(text=self.get_account_info_text(4))
        self.account_info_3.config(text=self.get_account_info_text(3))

        for subframe in self.subframes:
            subframe.update_text()

        self.label_room.config(text=tr("lobby.label.room"))
        self.button_create_room.config(text=tr("lobby.button.create_room"))
        self.button_join_room.config(text=tr("lobby.button.join_room"))

        self.settings_button.update_text()
