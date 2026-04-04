import tkinter as tk
from tkinter import ttk, messagebox

from .. import AbstractScreen
from ...autobot import AutoBot, ScriptNotFound, ScriptInstanceInitFail
from ...config import config, AutoBotInfo, AutoBotItemInfo
from ...language import tr
from ...scripts import ScriptClassWrapper

from ..settings.button import SettingsButton


class GameAssistantFrame:
    def __init__(self, parent, screen: AbstractScreen):
        self.parent = parent
        self.ui = screen.ui
        self.screen = screen

        self.first_row = tk.Frame(self.parent)
        self.first_row.grid(row=0, column=0)

        self.bot_select_label = tk.Label(self.first_row)
        self.bot_select_label.grid(row=0, column=0)

        self.refresh_button = tk.Button(self.first_row, command=self.update_bots_list)
        self.refresh_button.grid(row=0, column=1)

        self.bot_select_combobox = ttk.Combobox(self.parent)
        self.bot_select_combobox.grid(row=1, column=0)
        self.update_bots_list()

        self.running_bot: AutoBot | None = None
        for autobot_info in config.autobots:
            if autobot_info.name == config.default_autobot_name:
                self._set_running_bot_from_info(autobot_info)
                break

        self.bot_run_or_stop_button = tk.Button(self.parent, command=self.run_or_stop_button_clicked)
        self.bot_run_or_stop_button.grid(row=2, column=0)

        self.bot_running_label = tk.Label(self.parent)
        self.bot_running_label.grid(row=3, column=0)

        self.settings_button = SettingsButton(self.parent, self.screen)
        self.settings_button.grid(row=4, column=0, sticky="se")

    def update_text(self):
        self.bot_select_label.config(text=tr("game.assistant.bot_select"))
        if self.running_bot is None:
            self.bot_running_label.config(text="")
            self.bot_run_or_stop_button.config(text=tr("game.assistant.start"))
        else:
            self.bot_running_label.config(text=tr("game.assistant.running").format(self.running_bot.name))
            self.bot_run_or_stop_button.config(text=tr("game.assistant.stop"))
        self.refresh_button.config(text=tr("game.assistant.refresh"))
        self.settings_button.update_text()

    def update_bots_list(self):
        self.bot_select_combobox.config(values=[autobot.name for autobot in config.autobots])

    def _set_running_bot_from_info(self, autobot_info: AutoBotInfo):
        try:
            new_bot = AutoBot(self.ui.scripts_manager, autobot_info)
        except ScriptNotFound as e:
            item_info: AutoBotItemInfo = e.args[0]
            messagebox.showerror(tr("game.assistant.dialog.title_error"),
                                 tr("game.assistant.dialog.script_not_found").format(item_info.package_name,
                                                                                     item_info.class_name))
        except ScriptInstanceInitFail as e:
            script_class_wrapper: ScriptClassWrapper
            script_class_wrapper, exc = e.args
            package_name = script_class_wrapper.package_wrapper.get_name()
            script_name = script_class_wrapper.get_name()
            messagebox.showerror(tr("game.assistant.dialog.title_error"),
                                 tr("game.assistant.dialog.init_error").format(package_name, script_name) +
                                 '\n{}: {}'.format(type(exc).__name__, str(exc)))
        else:
            self.running_bot = new_bot

    def run_or_stop_button_clicked(self):
        if self.running_bot is None:
            bot_name = self.bot_select_combobox.get()

            for autobot_info in config.autobots:
                if autobot_info.name == bot_name:
                    self._set_running_bot_from_info(autobot_info)
                    break

        else:
            self.running_bot = None
        self.update_text()