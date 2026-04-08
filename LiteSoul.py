"""
This is the entry file for packing App on MacOS.
"""

try:
    import traceback
    import logging
    import datetime
    import os

    LOG_FOLDER = "log"
    LOG_CLEAR_LIMIT_DAY = 7

    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(LOG_CLEAR_LIMIT_DAY)

    if not os.path.isdir(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)

    for filename in os.listdir(LOG_FOLDER):
        full_path = os.path.join(LOG_FOLDER, filename)
        file_stat = os.stat(full_path)
        if file_stat.st_mtime < cutoff.timestamp():
            os.remove(full_path)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(os.path.join(LOG_FOLDER, f"log_{int(now.timestamp())}")),
                  logging.StreamHandler()]
    )

    from ui_client.ui import UIWithTray
    UIWithTray().mainloop()

except Exception as e:
    with open("fail_log.txt", 'w') as fp:
        traceback.print_exc(file=fp)
