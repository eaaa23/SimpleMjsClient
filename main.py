import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

from ui_client.ui import UI

if __name__ == '__main__':
    UI().mainloop()