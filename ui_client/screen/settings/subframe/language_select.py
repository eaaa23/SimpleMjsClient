import tkinter as tk
from tkinter import ttk

from ....config import config
from ....language import tr, get_available_languages, get_language_from_name

from .. import SettingsSubframe


class LanguageSelectFrame(SettingsSubframe):
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.language_select_label = tk.Label(self.parent)
        self.language_select_label.grid(row=0, column=0)

        self.language_select_combobox = ttk.Combobox(self.parent,
                                                     values=[tr("name", lang) for lang in get_available_languages()])
        self.language_select_combobox.set(tr("name"))
        self.language_select_combobox.grid(row=0, column=1)

    def apply(self):
        config.lang = get_language_from_name(self.language_select_combobox.get())

    def update_text(self):
        self.language_select_label.config(text=tr("settings.language"))
