# Lite MahjongSoul Client

![Version](https://img.shields.io/badge/version-0.0.1-blue)

> A simple client of Mahjong Soul made with python.

## Choose your language for README:

- [English](README.md)
- [简体中文](README_CN.md)


## Dependency

- python 3.13+
- packages:
- - websockets 15.0.1
- - aiohttp 3.9.0
- - culsans 0.11.0
- - PIL 12.0.0
- - protobuf 3.20.0 (protobuf must be this version)
- - sortedcontainers
- - pystray

Install:  
`pip install websockets aiohttp culsans pillow protobuf==3.20.0 sortedcontainers pystray`


## Run
- Clone the repo
- Run in repo directory
`python main.py`

## For Developers
- Submodule `mjs_client` should be kept as an independent module
- Do not upload `config.json`


## Disclaimer

Submodule `mjs_client/api` is a modified version of https://github.com/MahjongRepository/mahjong_soul_api 
with hook field supported.

## Pack Executable / App

Make sure you installed all [dependencies](#Dependency) before moving onto the followings.

### MacOS

- Install `py2app` with `pip install py2app`
- Find the location of python package `google.protobuf`. 
You can run `pip show google` to see its location.  
The folder should be like this:  
    ```
    google/
    └── protobuf/  
        ├── __init__.py  
        ├── ...
    ```
    Add a `__init__.py` file in the `google` folder:
    ```
    google/
    ├── __init__.py  
    └── protobuf/  
        ├── __init__.py  
        ├── ...
    ```

- Make sure your environment has no `pyinstaller` installed. 
Or just run `pip uninstall pyinstaller` then reinstall later.
- Clear `build`, `dist` and `.eggs` directories if exists.
- Run: `python setup.py py2app`
- Output App will be placed in the `dist` folder.

#### Custom Icon
- Replace `icon/src.png` with your custom icon picture (png). Keep it named `src.png`
- Run: `cd icon && ./makeicon.sh`

#### View Log Files
- Log files are stored inside app path: `Contents/Resources/log`. 
Every time the app launch, log files out of 7 days will be automatically removed.

### Windows

- Install `pyinstaller` with `pip install pyinstaller`
- Run `python pack_exe.py`
- Output file is `LiteSoul.zip`. Download and extract this file to install this program.
