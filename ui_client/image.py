from dataclasses import dataclass
import os
import tkinter as tk
from typing import Callable, Literal

from PIL import Image, ImageTk


"""
`rotation` show up multiple times in this file. 

rotation: int
Represent the times of counterclockwise rotation of `facing direction`

For example: if rotation=0 means facing north:
rotation=1 -> facing west
rotation=2 -> facing south
rotation=3 -> facing east

Note that `facing direction` differs from the wind position of player.
A player sitting in the north faces south.

In image editing, rotation=0 represents the original state of an image.
rotation=1 -> PIL.Image.ROTATE_90
rotation=2 -> PIL.Image.ROTATE_180
rotation=3 -> PIL.Image.ROTATE_270
"""


@dataclass
class _ImageCacheKey:
    """
    A few signatures of transformed image to meet caches.
    """
    width: int
    height: int
    alpha: float

    def __hash__(self):
        return hash((self.width, self.height, self.alpha))


class _Image:
    def __init__(self, path: str):
        self.path = path
        self.src: Image.Image = Image.open(self.path)

        # cache src.width and src.height because they are slow
        self.src_width = self.src.width
        self.src_height = self.src.height

        self.images: dict[_ImageCacheKey, list[ImageTk.PhotoImage]] = {}

    def get(self, rotation: int, scale: float, alpha: float) -> ImageTk.PhotoImage:
        new_width = round(self.src.width * scale)
        new_height = round(self.src.height * scale)
        alpha_int = round(256 * alpha)
        key = _ImageCacheKey(new_width, new_height, alpha_int)
        if key not in self.images:
            src_adjusted = self.src.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if alpha != 1.0:
                src_adjusted = src_adjusted.convert("RGBA")
                src_adjusted.putdata([(r, g, b, alpha_int) for r, g, b, _ in src_adjusted.getdata()])

            images = [src_adjusted,
                      src_adjusted.transpose(Image.ROTATE_90),
                      src_adjusted.transpose(Image.ROTATE_180),
                      src_adjusted.transpose(Image.ROTATE_270)]
            self.images[key] = [ImageTk.PhotoImage(img) for img in images]

        return self.images[key][rotation]


class _ImageManager:
    def __init__(self):
        self._src_images: dict[str, _Image] = {}

    def load_directory(self, path: str):
        for filename in os.listdir(path):
            if filename.endswith(".png"):
                self._src_images[filename] = _Image(os.path.join(path, filename))

    def __call__(self, filename: str, rotation: int = 0, scale: float = 1.0, alpha: float = 1.0) -> ImageTk.PhotoImage:
        return self._src_images[filename].get(rotation % 4, scale, alpha)


Img: _ImageManager = _ImageManager()
Img.load_directory("assets")


ROTATION_MATRICES: list[Callable[[int, int], tuple[int, int]]] = [
    lambda i, j: (i, j),
    lambda i, j: (j, -i),
    lambda i, j: (-i, -j),
    lambda i, j: (-j, i)
]

type Anchor = Literal['nw', 'sw', 'se', 'ne']

ANCHOR: list[Anchor] = [tk.NW, tk.SW, tk.SE, tk.NE]


def abs_anchor(rotation: int, rel_anchor: Anchor) -> Anchor:
    """Get the absolute anchor from relative anchor and rotation."""
    return ANCHOR[(ANCHOR.index(rel_anchor) + rotation) % 4]
