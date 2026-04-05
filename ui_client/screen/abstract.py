from collections.abc import Callable
import tkinter as tk
from typing import Any

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
        self._on_destroy_callback: Callable[[], Any] | None = None

        self.frame = tk.Frame(parent)
        self.frame.pack()

    def set_destroy_callback(self, callback: Callable[[], Any]):
        self._on_destroy_callback = callback

    def new_window(self, screen_type, *args, **kwargs):
        new_window = tk.Toplevel(self.frame)

        def on_closing_callback():
            self.toplevels.pop(id(new_window))
            self.update()

        new_screen: AbstractScreen = screen_type(new_window, self.ui, *args, **kwargs)
        new_screen.set_destroy_callback(on_closing_callback)

        new_window.protocol("WM_DELETE_WINDOW", new_screen._user_shut_window_protocol_callback)

        self.toplevels[id(new_window)] = new_screen

    def on_destroy(self):
        """
        To be called on:
        1. screen change (main screens)
        2. user click on "X" button of the window (Non-main screens)
        3. called close() (Non-main screens)
        """
        pass

    def on_user_shut_window(self) -> bool:
        """
        Affect non-main screens only.
        Only called on user click on "X" button of the window.
        :return: agree to shut the window or not.
        """
        return True

    def destroy(self):
        self.on_destroy()
        if self._on_destroy_callback:
            self._on_destroy_callback()
        self.frame.destroy()

    def close(self):
        self.destroy()
        self.parent.destroy()

    def _user_shut_window_protocol_callback(self):
        if self.on_user_shut_window():
            self.close()

    def update(self):
        self.update_text()

    def refresh(self):
        self.update_text()
        for screen in self.toplevels.values():
            screen.refresh()

    def update_text(self):
        pass
