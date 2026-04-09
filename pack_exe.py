import os
import shutil
import zipfile

import PyInstaller.__main__

PyInstaller.__main__.run(["LiteSoul.py", "--onefile", "--windowed", "--ico=assets/icon.png"])

shutil.move("dist/LiteSoul.exe", "LiteSoul.exe")

z = zipfile.ZipFile("LiteSoul.zip", 'w')
z.write("LiteSoul.exe")

def add_folder(zipf, folder_name: str):
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            zipf.write(os.path.join(root, file))


add_folder(z, "assets")
add_folder(z, "text")
add_folder(z, "scripts")
os.remove("LiteSoul.exe")
shutil.rmtree("build")
shutil.rmtree("dist")