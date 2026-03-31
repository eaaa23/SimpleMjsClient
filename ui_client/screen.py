import logging
from base64 import b64encode, b64decode
import tkinter as tk
from collections.abc import Callable
from functools import partial
from tkinter import ttk, messagebox
from typing import Sequence

from mjs_client.client import MahjongSoulClient, ClientPhase
from mjs_client.const import ModeInt, TIME_FIXED_ADD
from mjs_client.controller import ClientController
from mjs_client.game.gamephase import GamePhase
from mjs_client.game.gamestate import GameState, Open, Discard, OpenType
from mjs_client.game.game import Game
from mjs_client.game.operation import PlayTile, AbstractPlayTile, AbstractOperation, AbstractCallOperation
from mjs_client.room import Room
from mjs_client.level import get_match_level_dict
from mjs_client.rule import DetailRule, is_valid_point, get_default_rule

from .image import Img, ROTATION_MATRICES, abs_anchor
from .operation_buttons import OperationButtonGroup
from .tile_group import AbstractTileGroup, HandTileGroup, DiscardTileGroup, TileInfo, DoraGroup, CallSelectionGroup
from .config import config
from .language import tr, get_available_languages, get_language_from_name


class AbstractScreen:
    PHASE: int = ClientPhase.BLANK
    def __init__(self, parent, ui):
        self.ui = ui
        self.client: MahjongSoulClient = ui.client
        self.controller: ClientController = ui.controller
        self.parent = parent
        self.toplevels: dict[int, AbstractScreen] = {}

        self.frame = tk.Frame(parent)
        self.frame.pack()


    def new_window(self, screen_type, *args, **kwargs):
        new_window = tk.Toplevel(self.frame)

        def on_closing():
            self.toplevels[id(new_window)].destroy()
            self.toplevels.pop(id(new_window))
            new_window.destroy()
        new_window.protocol("WM_DELETE_WINDOW", on_closing)

        self.toplevels[id(new_window)] = screen_type(new_window, self.ui, *args, **kwargs)

    def destroy(self):
        self.frame.destroy()

    def update(self):
        self.update_text()

    def refresh(self):
        self.update_text()
        for screen in self.toplevels.values():
            screen.refresh()

    def update_text(self):
        pass

class BlankScreen(AbstractScreen):
    pass


class SettingsButton:
    def __init__(self, parent, screen: AbstractScreen):
        self.parent = parent
        self.screen = screen
        self.button = tk.Button(parent, command=self.on_click)

    def on_click(self):
        self.screen.new_window(SettingScreen)

    def grid(self, row, column, **kwargs):
        self.button.grid(row=row, column=column)

    def update_text(self):
        self.button.config(text=tr("button.settings"))


class LoginScreen(AbstractScreen):
    PHASE = ClientPhase.BEFORE_LOGIN
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.label_username = tk.Label(self.frame)
        self.label_username.grid(row=0, column=0)

        self.var_username = tk.StringVar()

        self.var_username.set(config.username.raw)
        self.entry_username = tk.Entry(self.frame, textvariable=self.var_username)
        self.entry_username.grid(row=0, column=1)

        self.label_password = tk.Label(self.frame)
        self.label_password.grid(row=1, column=0)

        self.var_password = tk.StringVar()
        self.var_password.set(config.password.raw)
        self.entry_password = tk.Entry(self.frame, textvariable=self.var_password, show="*")
        self.entry_password.grid(row=1, column=1)

        self.var_preserve_input = tk.BooleanVar()
        self.var_preserve_input.set(config.preserve_login)
        self.checkbutton_preserve_input = tk.Checkbutton(self.frame, variable=self.var_preserve_input)
        self.checkbutton_preserve_input.grid(row=2, column=1)

        self.login_button = tk.Button(self.frame, command=self.login)
        self.login_button.grid(row=3, column=1)

        self.settings_button = SettingsButton(self.frame, self)
        self.settings_button.grid(row=4, column=2)

        self.update_text()

    def login(self):
        self.controller.login(self.var_username.get(), self.var_password.get())

    def update_text(self):
        self.label_username.config(text=tr("login.username"))
        self.label_password.config(text=tr("login.password"))
        self.settings_button.update_text()
        self.checkbutton_preserve_input.config(text=tr("login.preserve_input"))
        self.login_button.config(text=tr("login.login"))

    def destroy(self):
        if self.var_preserve_input.get():
            config.username.raw = self.var_username.get()
            config.password.raw = self.var_password.get()
        config.preserve_login = self.var_preserve_input.get()
        self.ui.save_config()
        self.frame.destroy()


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



class RadiobuttonGroup:
    TK_VARTYPE = {int: tk.IntVar, str: tk.StringVar, bool: tk.BooleanVar}
    def __init__(self, parent, values: Sequence[int | str | bool],
                 grid_coord: tuple[int, int], init_value=None, command:Callable=None):
        self.frame = tk.Frame(parent)
        self.frame.grid(row=grid_coord[0], column=grid_coord[1])
        self.var = self.TK_VARTYPE[type(values[0])]()
        if init_value is not None:
            self.var.set(init_value)
        self.radiobuttons: dict[int | str | bool, tk.Radiobutton] = {}
        for i, value in enumerate(values):
            new_radiobutton = tk.Radiobutton(self.frame, variable=self.var, value=value)
            if command is not None:
                new_radiobutton.config(command=command)
            new_radiobutton.grid(row=0, column=i)
            self.radiobuttons[value] = new_radiobutton

    def __getitem__(self, item):
        return self.radiobuttons[item]

    def get(self):
        return self.var.get()

    def update_text(self, key_format):
        for value, button in self.radiobuttons.items():
            button.config(text=tr(key_format.format(value)))


class CreateRoomScreen(AbstractScreen):
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.label_player_count = tk.Label(self.frame)
        self.label_player_count.grid(row=0, column=0)
        self.group_player_count = RadiobuttonGroup(self.frame, (4, 3),
                                                   (0, 1), 4, self.on_player_count_change)


        self.label_is_east = tk.Label(self.frame)
        self.label_is_east.grid(row=1, column=0)
        self.group_is_east = RadiobuttonGroup(self.frame, (True, False),
                                              (1, 1), True)


        self.label_time_index = tk.Label(self.frame)
        self.label_time_index.grid(row=2, column=0)
        self.group_time_index = RadiobuttonGroup(self.frame, tuple(range(5)),
                                                 (2, 1), 2)

        self.label_init_point = tk.Label(self.frame)
        self.label_init_point.grid(row=3, column=0)
        self.var_init_point = tk.StringVar(value="25000")
        self.entry_init_point = tk.Entry(self.frame, textvariable=self.var_init_point)
        self.entry_init_point.grid(row=3, column=1)

        self.label_fandian = tk.Label(self.frame)
        self.label_fandian.grid(row=4, column=0)
        self.var_fandian = tk.StringVar(value="30000")
        self.entry_fandian = tk.Entry(self.frame, textvariable=self.var_fandian)
        self.entry_fandian.grid(row=4, column=1)

        self.label_jifei = tk.Label(self.frame)
        self.label_jifei.grid(row=5, column=0)
        self.group_jifei = RadiobuttonGroup(self.frame, (False, True),
                                            (5, 1), True)

        self.label_shiduan = tk.Label(self.frame)
        self.label_shiduan.grid(row=6, column=0)
        self.group_shiduan = RadiobuttonGroup(self.frame, (False, True),
                                              (6, 1), True)

        self.label_fanfu = tk.Label(self.frame)
        self.label_fanfu.grid(row=7, column=0)
        self.group_fanfu = RadiobuttonGroup(self.frame, (1, 2, 4),
                                            (7, 1), 1)

        self.label_ai_level = tk.Label(self.frame)
        self.label_ai_level.grid(row=8, column=0)
        self.group_ai_level = RadiobuttonGroup(self.frame, (1, 2),
                                               (8, 1), 1)

        self.button_create = tk.Button(self.frame, command=self.create_room)
        self.button_create.grid(row=9, column=1)

        self.update_text()

    def on_player_count_change(self):
        if self.group_player_count.get() == 4:
            self.var_init_point.set("25000")
            self.var_fandian.set("30000")
        else:
            self.var_init_point.set("35000")
            self.var_fandian.set("40000")

    def _valid_point(self, point_str: str) -> int:
        if not point_str.isdigit() or not is_valid_point(int(point_str)):
            return -1
        return int(point_str)

    def create_room(self):
        init_point = self._valid_point(self.var_init_point.get())
        fandian = self._valid_point(self.var_fandian.get())
        if init_point == -1 or fandian == -1:
            messagebox.showerror(tr("error.point.title"), tr("error.point.text"))
            return
        player_count = self.group_player_count.get()
        is_east = self.group_is_east.get()
        dora_count = get_default_rule(player_count).dora_count
        time_fixed, time_add = TIME_FIXED_ADD[self.group_time_index.get()]
        detail_rule = DetailRule(init_point=init_point, fandian=fandian, dora_count=dora_count, time_fixed=time_fixed,
                                 time_add=time_add, shiduan=self.group_shiduan.get(), can_jifei=self.group_jifei.get(),
                                 ai_level=self.group_ai_level.get(), fanfu=self.group_fanfu.get())
        self.controller.create_room(player_count, is_east, detail_rule)

    def update_text(self):
        self.parent.title(tr("lobby.create_room.title"))
        self.label_player_count.config(text=tr("lobby.create_room.player_count.label"))
        self.group_player_count.update_text("lobby.create_room.player_count.{}")
        self.label_is_east.config(text=tr("lobby.create_room.is_east.label"))
        self.group_is_east.update_text("lobby.create_room.is_east.{}")
        self.label_time_index.config(text=tr("lobby.create_room.time.label"))
        self.group_time_index.update_text("lobby.create_room.time.{}")
        self.label_init_point.config(text=tr("lobby.create_room.init_point"))
        self.label_fandian.config(text=tr("lobby.create_room.fandian"))
        self.label_jifei.config(text=tr("lobby.create_room.can_jifei.label"))
        self.group_jifei.update_text("lobby.create_room.can_jifei.{}")
        self.label_shiduan.config(text=tr("lobby.create_room.shiduan.label"))
        self.group_shiduan.update_text("lobby.create_room.shiduan.{}")
        self.label_fanfu.config(text=tr("lobby.create_room.fanfu.label"))
        self.group_fanfu.update_text("lobby.create_room.fanfu.{}")
        self.label_ai_level.config(text=tr("lobby.create_room.ai_level.label"))
        self.group_ai_level.update_text("lobby.create_room.ai_level.{}")
        self.button_create.config(text=tr("lobby.create_room.create"))


class JoinRoomScreen(AbstractScreen):
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.label_enter_room_id = tk.Label(self.frame)
        self.label_enter_room_id.grid(row=0, column=0)

        self.var_room_id = tk.StringVar()
        self.room_number_entry = tk.Entry(self.frame, textvariable=self.var_room_id)
        self.room_number_entry.grid(row=0, column=1)

        self.button_join = tk.Button(self.frame, command=self.join)
        self.button_join.grid(row=1, column=1)

        self.update_text()

    def join(self):
        room_id_str = self.var_room_id.get()
        if not room_id_str.isdigit():
            messagebox.showerror(tr("error.room_id.title"), tr("error.room_id.text"))
            return
        room_id = int(room_id_str)
        self.controller.join_room(room_id)

    def update_text(self):
        self.parent.title(tr("lobby.join_room.title"))
        self.label_enter_room_id.config(text=tr("lobby.join_room.id"))
        self.button_join.config(text=tr("lobby.join_room.join"))


class RoomSeatFrame:
    def __init__(self, parent, ui, seat: int):
        self.parent = parent
        self.ui = ui
        self.seat = seat
        self.room: Room = self.ui.client.room

        self.name_label = tk.Label(self.parent)
        self.name_label.grid(row=0, column=0)

        self.ready_label = tk.Label(self.parent)
        self.ready_label.grid(row=1, column=0)

        self.button = tk.Button(self.parent, command=self.button_clicked)
        self.button.grid(row=2, column=0)
        self.seat_filled: bool = False

    def update(self):
        this_seat = self.room.seats[self.seat]
        self.seat_filled = (this_seat.account_id != 0)

        self.name_label.config(text=tr("room.bot") if this_seat.is_robot else this_seat.nickname)
        self.ready_label.config(text=tr("room.ready.{}".format(str(this_seat.ready))))

        if self.seat_filled:
            self.button.config(text=tr("room.button.remove"))
        else:
            self.button.config(text=tr("room.button.add"))

        if self.room.is_owner() and this_seat.account_id != self.ui.client.account_id:
            self.button.config(state=tk.NORMAL)
        else:
            self.button.config(state=tk.DISABLED)

    def button_clicked(self):
        if self.seat_filled:
            self.ui.controller.room_kick(self.seat)
        else:
            self.ui.controller.room_add_bot(self.seat)


class RoomScreen(AbstractScreen):
    PHASE = ClientPhase.INROOM
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.label_room_id = tk.Label(self.frame)
        self.label_room_id.grid(row=0, column=0)

        self.button_quit = tk.Button(self.frame, command=self.controller.leave_room)
        self.button_quit.grid(row=0, column=1)

        self.button_ready_or_start = tk.Button(self.frame, command=self.ready_or_start_button_clicked)
        self.button_ready_or_start.grid(row=0, column=2)

        self.seat_frames: list[RoomSeatFrame] = []
        for c in range(self.client.room.player_count):
            new_seat_frame = tk.Frame(self.frame, borderwidth=1, relief=tk.RAISED)
            new_seat_frame.grid(row=1, column=c)
            self.seat_frames.append(RoomSeatFrame(new_seat_frame, ui, c))

        self.settings_button = SettingsButton(self.frame, self)
        self.settings_button.grid(row=2, column=self.client.room.player_count)

        self.update_text()

    def ready_or_start_button_clicked(self):
        if self.client.room.is_owner():
            self.controller.room_start()
        else:
            self.controller.room_ready(ready=False, switch=True)

    def update_text(self):
        self.label_room_id.config(text=tr("room.id").format(self.client.room.room_id))
        self.button_quit.config(text=tr("room.button.quit"))
        if self.client.room.is_owner():
            self.button_ready_or_start.config(text=tr("room.button.start"),
                                              state=tk.NORMAL if self.client.room.all_ready() else tk.DISABLED)
        else:
            self.button_ready_or_start.config(text=tr("room.button.ready_cancel") if self.client.room.me().ready else tr("room.button.ready"))
        for subframe in self.seat_frames:
            subframe.update()
        self.settings_button.update_text()



class Liqibang:
    def __init__(self, canvas: tk.Canvas, center: tuple[int, int], size: tuple[int, int], radius: int, rotation: int):
        self.canvas = canvas
        self.center = center
        self.rotation = rotation
        self.size = ROTATION_MATRICES[rotation](*size)

        xc, yc = center
        dx, dy = self.size[0] // 2, self.size[1] // 2
        self.rect: tuple[int, int, int, int] = (xc - dx, yc - dy, xc + dx, yc + dy)
        self.circle_rect: tuple[int, int, int, int] = (xc - radius, yc - radius, xc + radius, yc + radius)

        self.rect_id = 0
        self.circle_id = 0
        self.created = False

    def draw(self, draw: bool):
        if draw and not self.created:
            self.rect_id = self.canvas.create_rectangle(self.rect, fill="white")
            self.circle_id = self.canvas.create_oval(self.circle_rect, fill="red", width=0)
            self.created = True
        elif not draw and self.created:
            self.canvas.delete(self.rect_id)
            self.canvas.delete(self.circle_id)
            self.created = False



class CallSelectionSubframe:
    def __init__(self, call_selection_group: CallSelectionGroup, rect_size: tuple[int, int]):
        self.group = call_selection_group
        self.canvas = self.group.canvas
        self.rect: tuple[int, int, int, int] = (self.group.origin[0], self.group.origin[1],
                                                self.group.origin[0] + rect_size[0], self.group.origin[1] + rect_size[1])
        self.rect_id: int = 0
        self.created: bool = False

    def draw(self, operation_list: list[AbstractCallOperation]):
        if not self.created:
            self.rect_id = self.canvas.create_rectangle(self.rect, fill="lightblue", width=0)
            self.group.set_operation_list(operation_list)
            self.group.redraw()
            self.created = True

    def clear(self):
        if self.created:
            self.canvas.delete(self.rect_id)
            self.group.set_operation_list([])
            self.group.redraw()
            self.created = True


class GameScreen(AbstractScreen):
    PHASE = ClientPhase.INGAME
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 800
    CANVAS_MID_X = CANVAS_WIDTH // 2
    CANVAS_MID_Y = CANVAS_HEIGHT // 2
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.game: Game = self.client.game
        self.game_state: GameState = self.client.game.action_handler.game_state

        self.canvas = tk.Canvas(self.frame, width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT)
        self.canvas.grid(row=0, column=0)

        self.canvas.create_rectangle(self.CANVAS_MID_X-120, self.CANVAS_MID_Y-120, self.CANVAS_MID_X+120, self.CANVAS_MID_Y+120,
                                     outline="black")

        self.operation_button_group = OperationButtonGroup(self, (648, 732), tk.SE, (64, 25))
        self.call_selection_subframe = CallSelectionSubframe(CallSelectionGroup(self.canvas, self.game_state, (200, 675), 0, 0.4,
                                                                                self.tile_bind_func),
                                                             (320, 50))

        self.hand_tile_groups: list[HandTileGroup] = []
        self.discard_groups: list[DiscardTileGroup] = []
        self.player_text: list[tk.Label] = []
        self.wind_text: list[tk.Label] = []
        self.liqibangs: list[Liqibang] = []
        for rotation in range(4):
            rot_matrix = ROTATION_MATRICES[rotation]
            # hand
            rel_x, rel_y = rot_matrix(-312, 332)
            self.hand_tile_groups.append(HandTileGroup(self.canvas, self.game_state, self.operation_button_group,
                                                       (self.CANVAS_MID_X+rel_x, self.CANVAS_MID_Y+rel_y),
                                                       rotation, 0.5, self.tile_bind_func))

            # player text
            new_label = tk.Label(self.canvas)
            self.player_text.append(new_label)
            self.canvas.create_window(self.CANVAS_MID_X + rel_x, self.CANVAS_MID_Y + rel_y,
                                      anchor=abs_anchor(rotation, tk.SW), window=new_label)

            # center (wind) text
            rel_x, rel_y = rot_matrix(-90, 110)
            new_label = tk.Label(self.canvas)
            self.wind_text.append(new_label)
            self.canvas.create_window(self.CANVAS_MID_X + rel_x, self.CANVAS_MID_Y + rel_y,
                                      anchor=abs_anchor(rotation, tk.SW), window=new_label)

            # discard
            rel_x, rel_y = rot_matrix(-120, 120)
            self.discard_groups.append(DiscardTileGroup(self.canvas, self.game_state,
                                                        (self.CANVAS_MID_X+rel_x, self.CANVAS_MID_Y+rel_y),
                                                        rotation, 0.5))
            # liqibang
            rel_x, rel_y = rot_matrix(0, 105)
            self.liqibangs.append(Liqibang(self.canvas, (self.CANVAS_MID_X+rel_x, self.CANVAS_MID_Y+rel_y),
                                           (130, 16), 3, rotation))

        self.label_chang = tk.Label(self.canvas)
        self.canvas.create_window(self.CANVAS_MID_X, self.CANVAS_MID_Y - 90, anchor=tk.N, window=self.label_chang)
        self.liqibang_changgong = Liqibang(self.canvas, (self.CANVAS_MID_X - 30, self.CANVAS_MID_Y - 20),
                                           (60, 8), 2, 1)
        self.label_changgong = tk.Label(self.canvas)
        self.canvas.create_window(self.CANVAS_MID_X, self.CANVAS_MID_Y - 20, anchor=tk.W, window=self.label_changgong)
        self.dora_group = DoraGroup(self.canvas, self.game_state,
                                    (self.CANVAS_MID_X - 60, self.CANVAS_MID_Y + 20), 0, 0.3)

        self.frame_round_result = tk.Frame(self.canvas, bg='lightblue')
        self.frame_round_result_id: int = 0
        self.label_round_result = tk.Label(self.frame_round_result)
        self.label_round_result.grid(row=1, column=1)
        self.labels_delta_scores: list[tk.Label] = [tk.Label(self.frame_round_result, bg='lightblue') for i in range(4)]
        self.labels_delta_scores[0].grid(row=2, column=1)
        self.labels_delta_scores[1].grid(row=1, column=2)
        self.labels_delta_scores[2].grid(row=0, column=1)
        self.labels_delta_scores[3].grid(row=1, column=0)
        self.button_confirm_round_result = tk.Button(self.frame_round_result, command=self.confirm_button_func)
        self.button_confirm_round_result.grid(row=2, column=2)
        self.round_results_displaying = False

        self.show_end_screen = False


    def update(self):
        self.operation_button_group.update()
        self.call_selection_subframe.clear()
        for rotation in range(4):
            self.hand_tile_groups[rotation].redraw()
            self.discard_groups[rotation].redraw()
            self.update_label_text_and_liqi(rotation)
        self.label_chang.config(text=tr("game.round.{}".format(self.game_state.current_chang)).format(self.game_state.current_ju+1, self.game_state.current_benchang) + '\n' +
                                tr("game.remain").format(self.game_state.left_tile_count))
        self.liqibang_changgong.draw(True)
        self.label_changgong.config(text="x {}".format(self.game_state.liqibang))
        self.dora_group.redraw()
        #logging.info(f"GameScreen update: show_end_screen={self.show_end_screen}, phase={self.game_state.phase}")
        #logging.info(f"Round results label config: {self.label_round_result.config()}")
        if self.game_state.phase == GamePhase.BETWEEN_ROUNDS:
            if not self.show_end_screen:
                self.label_round_result.config(text=self.get_round_result_text())
                self.frame_round_result_id = self.canvas.create_window(self.CANVAS_MID_X, self.CANVAS_MID_Y, anchor=tk.CENTER, window=self.frame_round_result)
                for rotation in range(4):
                    seat = (self.game_state.my_seat + rotation) % 4
                    if seat >= self.game_state.player_count:
                        delta_score_text = ""
                    else:
                        delta_score_text = "{:+d}".format(self.game_state.round_result.delta_scores[seat])
                    self.labels_delta_scores[rotation].config(text=delta_score_text)
                self.button_confirm_round_result.config(text=tr("game.confirm"))
                self.round_results_displaying = True
                logging.info("Round result frame display")
        elif self.round_results_displaying:
            self.canvas.delete(self.frame_round_result_id)
            self.round_results_displaying = False
            logging.info("Round result frame destroyed")

    def get_round_result_text(self) -> str:
        lines = []
        for win_info in self.game_state.round_result.win:
            player_name = self.game.player_names[win_info.seat]
            if not player_name:
                player_name = tr("room.bot")
            lines.append(tr("game.win.tsumo" if win_info.tsumo else "game.win.ron").format(player_name))
            if win_info.yakuman:
                line_fmt = tr("game.win.yakuman_line")
                for yaku_id, value in win_info.yakus.items():
                    yaku_name = tr("game.win.yaku.{}".format(yaku_id))
                    lines.append(line_fmt.format(yaku_name))
                lines.append(tr("game.win.value_yakuman.{}".format(win_info.fan)).format(win_info.score))
            else:
                line_fmt = tr("game.win.yaku_line")
                for yaku_id, value in win_info.yakus.items():
                    yaku_name = tr("game.win.yaku.{}".format(yaku_id))
                    lines.append(line_fmt.format(yaku_name, value))
                lines.append(tr("game.win.value").format(win_info.fan, win_info.fu, win_info.score))
        return "\n".join(lines)

    def get_game_result_text(self) -> str:
        lines = []
        for rank, end_result in enumerate(self.game_state.game_result):
            lines.append(tr("game.result").format(rank+1, self.game.player_names[end_result.seat], end_result.point, end_result.score, end_result.pt))
        return "\n".join(lines)


    def update_label_text_and_liqi(self, rotation: int):
        seat = (self.game_state.my_seat + rotation) % 4
        if seat >= self.game_state.player_count:
            return
        wind_position = (seat - self.game_state.current_ju) % 4
        player_name = self.game.player_names[seat]
        if player_name == "":
            player_name = tr("room.bot")
        self.player_text[rotation].config(text=(player_name + "\n" + str(self.game_state.scores[seat])))
        self.wind_text[rotation].config(text=tr("game.wind.{}".format(wind_position)))
        self.liqibangs[rotation].draw(bool(self.game_state.player_liqis[seat]))

    def tile_bind_func(self, op: AbstractOperation, event: tk.Event):
        self.controller.game_put_operation(op)

    def put_operation(self, op: AbstractOperation):
        self.controller.game_put_operation(op)

    def confirm_button_func(self):
        logging.info(f"Confirm button: ended={self.game_state.ended}")
        if self.game_state.ended:
            if self.show_end_screen:
                self.controller.return_from_game()
            else:
                self.show_end_screen = True
                for rotation in range(4):
                    self.labels_delta_scores[rotation].config(text="")
                self.label_round_result.config(text=self.get_game_result_text())
        else:
            self.controller.game_confirm_new_round()


class SettingScreen(AbstractScreen):
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.language_select_label = tk.Label(self.frame)
        self.language_select_label.grid(row=0, column=0)

        self.language_select_combobox = ttk.Combobox(self.frame, values=[tr("name", lang) for lang in get_available_languages()])
        self.language_select_combobox.set(tr("name"))
        self.language_select_combobox.grid(row=0, column=1)

        self.apply_button = tk.Button(self.frame, command=self.apply)
        self.apply_button.grid(row=1, column=2)

        self.update_text()

    def apply(self):
        config.lang = get_language_from_name(self.language_select_combobox.get())
        self.ui.save_config()

    def update_text(self):
        self.parent.title(tr("button.settings"))
        self.language_select_label.config(text=tr("settings.language"))
        self.apply_button.config(text=tr("settings.apply"))

    def destroy(self):
        self.apply()
        self.frame.destroy()



_MAIN_SCREENS = [BlankScreen, LoginScreen, LobbyScreen, RoomScreen, GameScreen]
MAIN_SCREENS = {scr_type.PHASE: scr_type for scr_type in _MAIN_SCREENS}
