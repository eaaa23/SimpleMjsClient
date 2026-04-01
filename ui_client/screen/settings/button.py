import tkinter as tk

from ...language import tr

from ..abstract import AbstractScreen

from . import SettingScreen


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