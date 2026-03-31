# Lite MahjongSoul Client

![Version](https://img.shields.io/badge/version-0.0.1-blue)

> A simple client of Mahjong Soul made with python.


## Dependency

- python 3.13+
- packages:
- - websockets 15.0.1
- - aiohttp 3.9.0
- - culsans 0.11.0
- - PIL 12.0.0
- - protobuf 3.20.0 (protobuf must be this version)

Install:  
`pip install websockets==15.0.1 aiohttp==3.9.0 culsans==0.11.0 pillow==12.0.0 protobuf==3.20.0`


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

### MacOS

- Install `py2app` with `pip install py2app`
- Make sure your environment has no `pyinstaller` installed. 
Or just run `pip uninstall pyinstaller` then reinstall later.
- Clear `build`, `dist` and `.eggs` directories if exists.
- Run: `python setup.py py2app`
- Output App will be placed in the `dist` folder.

#### Custom Icon
- You can replace `icon/src.png` and regenerate the `icon.icns`
in the `icon` folder using `makeicon.sh`.

#### View Log Files
- Log files are stored inside app path: `Contents/Resources/log`. 
Every time the app launch, log files out of 7 days will be automatically removed.

### Windows

- Yet to be developed.