import logging
import platform

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

from ui_client.ui import UI, UIWithTray

if __name__ == '__main__':
    system = platform.system()
    if system in ("Windows", "Darwin"):
        logging.info("Launcher: system tray enabled")
        ui = UIWithTray()
    else:
        logging.info("Launcher: system not found, system tray disbled")
        ui = UI()
    ui.mainloop()
