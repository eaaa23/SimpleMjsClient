import logging
import tkinter as tk
from tkinter import messagebox
import json
from functools import partial

from mjs_client.client import MahjongSoulClient
from mjs_client.controller import ClientController
from mjs_client.exceptions import MjsError

from .config import Config, get_config, config
from .screen import AbstractScreen, LoginScreen, MAIN_SCREENS, BlankScreen
from .language import set_language, tr, TEXT_FOLDER

class UI:
    def __init__(self):
        self.apply_config()

        self.root = tk.Tk()
        self.root.title(tr("title"))

        self.client = MahjongSoulClient()
        self.controller = ClientController(self.client)

        self.controller.set_update_trigger(partial(self.root.event_generate, "<<Update>>"))
        self.root.bind("<<Update>>", self.update)

        self.controller.set_error_hook(self.error_hook)

        self.controller.start()

        self.current_screen: AbstractScreen = BlankScreen(self.root, self)

        self.controller.connect(ssl=False)

    def apply_config(self):
        set_language(config.lang)

    def refresh(self):
        self.root.title(tr("title"))
        self.current_screen.refresh()

    def save_config(self, refresh=True):
        config.save()
        self.apply_config()
        if refresh:
            self.refresh()

    def mainloop(self):
        self.root.mainloop()

    def update(self, event):
        logging.info("UI.update")
        if self.client.phase != self.current_screen.PHASE:
            logging.info(f"UI change current screen, from {self.current_screen.PHASE} to {self.client.phase}")
            self.change_current_screen(MAIN_SCREENS[self.client.phase])
        self.current_screen.update()
        self.root.update_idletasks()

    def change_current_screen(self, screen_type):
        self.current_screen.destroy()
        self.current_screen = screen_type(self.root, self)

    def error_hook(self, e: MjsError):
        error_title = tr("error.{}.title").format(e.TEXT_KEY)
        error_text = tr("error.{}.code.{}".format(e.TEXT_KEY, e.args[0]))
        if not error_text:
            error_text = tr("error.{}.default".format(e.TEXT_KEY)) + "\n"
            error_text += tr("error.error_code").format(e.args[0])
        logging.error(f"{type(e).__name__} {e}")
        messagebox.showerror(error_title, error_text)


