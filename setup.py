"""
This setup.py is for generating App on MacOS.
Usage: python setup.py py2app
"""

from setuptools import setup


# PIL is automatically included by py2app
APP = ["LiteSoul.py"]
PACKAGES = ["websockets", "aiohttp", "culsans", "google"]
PROJECT_PACKAGES = []
RESOURCES = ["text", "assets", "scripts"]
ICONFILE = "icon/icon.icns"
OPTIONS = {
    "packages": PACKAGES + PROJECT_PACKAGES,
    "resources": RESOURCES,
    "iconfile": ICONFILE
}

setup(
    app=APP,
    data_files=[],
    options={"py2app": OPTIONS},
    setup_requires=["py2app"] + PACKAGES
)