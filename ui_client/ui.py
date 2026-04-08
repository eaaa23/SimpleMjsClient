from functools import partial
import logging
import tkinter as tk
from tkinter import messagebox

from PIL import Image
import pystray
from pystray import MenuItem

from mjs_client.client import MahjongSoulClient
from mjs_client.controller import ClientController
from mjs_client.exceptions import MjsError

from .config import config
from .language import set_language, tr
from .screen import AbstractScreen, MAIN_SCREENS, BlankScreen
from .scripts import PackageScriptManager


class UI:
    def __init__(self):
        self.apply_config()

        self.scripts_manager = PackageScriptManager()
        self.scripts_manager.sync_scripts_folder()

        self.root = tk.Tk()
        self.root.title(tr("title"))

        self.background = False   # This will always be False unless in UIWithTray

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
        # logging.info("UI.update")
        if self.client.phase != self.current_screen.PHASE:
            logging.info(f"UI change current screen, from {self.current_screen.PHASE} to {self.client.phase}")
            self.change_current_screen(MAIN_SCREENS[self.client.phase])
        self.current_screen.update(self.background)
        if not self.background:
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


class UIWithTray(UI):
    def __init__(self):
        super().__init__()
        self.tray_menu = pystray.Menu(MenuItem(tr("tray.show"), self.show_from_tray),
                                      MenuItem(tr("tray.quit"), self.quit_from_tray))
        self.tray_icon = pystray.Icon("MjsClient", Image.open("assets/tray.png"), tr("title"), self.tray_menu)
        self.tray_icon.run_detached()
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

    def hide(self):
        """
        Hook on user clicking "X" on the root window. Hook to tkinter WM_DELETE_WINDOW
        """
        self.root.withdraw()
        self.background = True
        if self.tray_icon:
            self.tray_icon.visible = True

    def show_from_tray(self, icon=None, item=None):
        """
        Hook to show window by tray icon.
        """
        self.background = False
        if icon:
            icon.visible = True
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.update(None)

    def quit_from_tray(self, icon=None, item=None):
        """
        Hook to quit app by tray icon.
        """
        self.root.quit()
        self.root.destroy()
