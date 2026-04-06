import tkinter as tk
from tkinter import messagebox
from typing import Sequence, Callable, cast

from mjs_client.const import TIME_FIXED_ADD, PlayerCount
from mjs_client.rule import is_valid_point, get_default_rule, DetailRule

from ...language import tr

from ..abstract import AbstractScreen


class RadiobuttonGroup:
    TK_VARTYPE = {int: tk.IntVar, str: tk.StringVar, bool: tk.BooleanVar}

    def __init__(self, parent, values: Sequence[int | str | bool],
                 grid_coord: tuple[int, int], init_value=None, command: Callable = None):
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
        player_count: PlayerCount = cast(PlayerCount, self.group_player_count.get())
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
