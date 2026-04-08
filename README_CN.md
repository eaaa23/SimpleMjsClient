# Lite MahjongSoul Client / 雀魂麻将客户端丐版

![Version](https://img.shields.io/badge/version-0.0.1-blue)
 
> 一个简单的python自制雀魂客户端


## 依赖项

- Python 3.13+
- Python包:
- - websockets 15.0.1
- - aiohttp 3.9.0
- - culsans 0.11.0
- - PIL 12.0.0
- - protobuf 3.20.0 (protobuf must be this version / 必须为此版本)
- - sortedcontainers

安装:  
`pip install websockets aiohttp culsans pillow protobuf==3.20.0 sortedcontainers pystray`


## 运行
- 克隆此仓库
- 在仓库目录下运行
`python main.py`

## 开发者
- 子模块 `mjs_client` 应该保持为一个独立的模块，不应依赖GUI.
- 不要上传 `config.json`


## 声明

子模块 `mjsclient/api` 改自 https://github.com/MahjongRepository/mahjong_soul_api 。


## 将项目打包成可执行文件或App

确保你的所有[依赖](#依赖项)都已安装完毕。

### MacOS

- 安装 `py2app`:  `pip install py2app`
- 找到 `google.protobuf`包的安装路径。可以使用`pip show google`来查看。   
打开安装路径，文件夹结构应如下所示:  
    ```
    google/
    └── protobuf/  
        ├── __init__.py  
        ├── ...
    ```
    在`google`文件夹下添加一个`__init__.py`：
    ```
    google/
    ├── __init__.py  
    └── protobuf/  
        ├── __init__.py  
        ├── ...
    ```

- 确保你的环境下没有`pyinstaller`.
可以先运行 `pip uninstall pyinstaller` 后续再重新安装`pyinstaller`.
- 清空 `build`, `dist` 和 `.eggs` 文件夹下的内容，如果它们存在。
- 运行: `python setup.py py2app`
- 输出的App在 `dist` 文件夹下。

#### 自定义App图标
- 将 `icon/src.png` 替换为你想要使用的App图标图片(png格式)
- 运行 `cd icon && ./makeicon.sh`

#### 查看App Log
- 日志文件被存储在App内部的目录: `Contents/Resources/log`. 
每当App启动时，距今7日以前的日志文件会被自动删除。

### Windows

- 仍在开发中。