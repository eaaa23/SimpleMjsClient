import tkinter as tk

from mjs_client.client import ClientPhase

from ..config import config
from ..language import tr

from .abstract import AbstractScreen
from .settings.button import SettingsButton


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

    def on_destroy(self):
        if self.var_preserve_input.get():
            config.username.raw = self.var_username.get()
            config.password.raw = self.var_password.get()
        config.preserve_login = self.var_preserve_input.get()
        self.ui.save_config()
