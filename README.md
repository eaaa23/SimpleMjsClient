# Lite MahjongSoul Client / 雀魂麻将客户端丐版

![Version](https://img.shields.io/badge/version-0.0.1-blue)

> A simple client of Mahjong Soul made with python.  
> 一个简单的python自制雀魂客户端


## Dependency

- python 3.13+
- packages:
- - websockets 15.0.1
- - aiohttp 3.9.0
- - culsans 0.11.0
- - protobuf 3.20.0 (protobuf must be this version / 必须为此版本)

Install:  
`pip install websockets==15.0.1 aiohttp==3.9.0 culsans==0.11.0 protobuf==3.20.0`


## Run
- Clone the repo
- Run in repo directory
`python main.py`

## For Developers
- Submodule `mjsclient` should be kept as an independent module
- Do not upload config.json


## Disclaimer

Submodule `mjsclient/api` is a modified version of https://github.com/MahjongRepository/mahjong_soul_api 
with hook field supported.