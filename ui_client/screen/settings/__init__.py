import tkinter as tk

from ...language import tr

from ..abstract import AbstractScreen

from .subframe import SettingsSubframe
from .subframe.language_select import LanguageSelectFrame
from .subframe.scripts import ScriptsFrame
from .subframe.autobot import AutoBotSettingsFrame


class SettingScreen(AbstractScreen):
    SUBFRAME_CLASSES = [LanguageSelectFrame, ScriptsFrame, AutoBotSettingsFrame]
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        row = 0
        self.subframes: list[SettingsSubframe] = []
        for row, subframe_class in enumerate(self.SUBFRAME_CLASSES):
            new_tk_frame = tk.Frame(self.frame)
            new_tk_frame.grid(row=row, column=0, sticky="w")
            self.subframes.append(subframe_class(new_tk_frame, self))

        self.apply_button = tk.Button(self.frame, command=self.apply)
        self.apply_button.grid(row=row+1, column=1, sticky=tk.SE)

        self.update_text()

    def apply(self):
        for subframe in self.subframes:
            subframe.apply()
        self.ui.save_config()

    def update_text(self):
        self.parent.title(tr("button.settings"))
        for subframe in self.subframes:
            subframe.update_text()
        self.apply_button.config(text=tr("settings.apply"))

    def on_destroy(self):
        self.apply()