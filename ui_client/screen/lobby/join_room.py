import tkinter as tk
from tkinter import messagebox

from ...language import tr

from ..abstract import AbstractScreen


class JoinRoomScreen(AbstractScreen):
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.label_enter_room_id = tk.Label(self.frame)
        self.label_enter_room_id.grid(row=0, column=0)

        self.var_room_id = tk.StringVar()
        self.room_number_entry = tk.Entry(self.frame, textvariable=self.var_room_id)
        self.room_number_entry.grid(row=0, column=1)
        self.room_number_entry.bind("<Return>", lambda e: self.join())

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

