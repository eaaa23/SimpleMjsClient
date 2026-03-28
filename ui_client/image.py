import tkinter as tk
from typing import Callable
import os

from PIL import Image, ImageTk


class _Image:
    def __init__(self, path: str):
        self.path = path
        self.src: Image.Image = None
        self.images: dict[tuple[int, int, float], list[Image.Image]] = {}

    def get(self, rotation: int, scale: float, alpha: float) -> Image.Image:
        if self.src is None:
            self.src = Image.open(self.path)
        new_width = round(self.src.width * scale)
        new_height = round(self.src.height * scale)
        if (new_width, new_height, alpha) not in self.images:
            src_adjusted = self.src.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if alpha != 1.0:
                src_adjusted = src_adjusted.convert("RGBA")
                a = round(256 * alpha)
                src_adjusted.putdata([(r, g, b, a) for r, g, b, _ in src_adjusted.getdata()])
            self.images[new_width, new_height, alpha] = [src_adjusted,
                                                  src_adjusted.transpose(Image.ROTATE_90),
                                                  src_adjusted.transpose(Image.ROTATE_180),
                                                  src_adjusted.transpose(Image.ROTATE_270)]

        return self.images[new_width, new_height, alpha][rotation]


class _ImageManager:
    def __init__(self):
        self._src_images: dict[str, _Image] = {}

    def load_directory(self, path: str):
        for filename in os.listdir(path):
            if filename.endswith(".png"):
                self._src_images[filename] = _Image(os.path.join(path, filename))

    def __call__(self, filename: str, rotation: int = 0, scale: float = 1.0, alpha: float = 1.0) -> ImageTk.PhotoImage:
        return ImageTk.PhotoImage(self._src_images[filename].get(rotation % 4, scale, alpha))


Img: _ImageManager = _ImageManager()
Img.load_directory("assets")


ROTATION_MATRICES: list[Callable[[int, int], tuple[int, int]]] = [
    lambda i, j: (i, j),
    lambda i, j: (j, -i),
    lambda i, j: (-i, -j),
    lambda i, j: (-j, i)
]

ANCHOR = [tk.NW, tk.SW, tk.SE, tk.NE]

def abs_anchor(rotation, rel_anchor):
    """Get absolute anchor"""
    return ANCHOR[(ANCHOR.index(rel_anchor) + rotation) % 4]