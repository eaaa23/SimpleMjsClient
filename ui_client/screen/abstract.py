import tkinter as tk

from mjs_client.client import ClientPhase, MahjongSoulClient
from mjs_client.controller import ClientController


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
