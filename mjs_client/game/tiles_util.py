from typing import Iterable


def tile_sort_key(tile: str) -> int:
    return {'m': 0, 'p': 10, 's': 20, 'z': 30}[tile[1]] + (5 if tile[0] == '0' else int(tile[0]))


def turn0to5(tiles: Iterable[str]) -> list[str]:
    return [tile.replace('0', '5') for tile in tiles]


VALID_TILES: tuple[str, ...] = (tuple(f"{i}{t}" for t in ("m", "p", "s") for i in range(10))
                                + tuple(f"{i}z" for i in range(1, 8)))
INDEX34_TO_TILE: tuple[str, ...] = (tuple(f"{i}{t}" for t in ("m", "p", "s") for i in range(1, 10))
                                    + tuple(f"{i}z" for i in range(1, 8)))

TILES_TO_INDEX34: dict[str, int] = {tile: idx for idx, tile in enumerate(INDEX34_TO_TILE)}
TILES_TO_INDEX34['0s'] = TILES_TO_INDEX34['5s']
TILES_TO_INDEX34['0m'] = TILES_TO_INDEX34['5m']
TILES_TO_INDEX34['0p'] = TILES_TO_INDEX34['5p']

SANMA_INVALID_TILES = {f'{i}m' for i in (0, 2, 3, 4, 5, 6, 7, 8)}
