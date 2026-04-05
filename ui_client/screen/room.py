import tkinter as tk

from mjs_client.client import ClientPhase
from mjs_client.room import Room

from ..language import tr

from .abstract import AbstractScreen
from .settings.button import SettingsButton


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
