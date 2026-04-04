from typing import List, Iterable, Dict, Callable, Tuple


def tile_cmp_key(tile: str) -> int:
    return {'m': 0, 'p': 10, 's': 20, 'z': 30}[tile[1]] + (5 if tile[0] == '0' else int(tile[0]))

def turn0to5(tiles: Iterable[str]) -> List[str]:
    return [tile.replace('0', '5') for tile in tiles]

def count_tiles(tiles: Iterable[str]) -> Dict[str, int]:
    retval = {}
    for tile in tiles:
        retval[tile] = retval.get(tile, 0) + 1
    return retval

def get_indexes(tiles: Iterable[str], target: str) -> Iterable[int]:
    return (idx for idx, tile in enumerate(tiles) if tile == target)

def get_indexes_by_count_condition(tiles: Iterable[str], cond: Callable[[int], bool]) -> Iterable[int]:
    tiles_list = list(tiles)
    count = count_tiles(tiles_list)
    return (idx for idx, tile in enumerate(tiles_list) if cond(count[tile]))


VALID_TILES: Tuple[str, ...] = tuple(f"{i}{t}" for t in ("m", "p", "s") for i in range(10)) + tuple(f"{i}z" for i in range(1, 8))
INDEX34_TO_TILE: Tuple[str, ...] = tuple(f"{i}{t}" for t in ("m", "p", "s") for i in range(1, 10)) + tuple(f"{i}z" for i in range(1, 8))

TILES_TO_INDEX34: Dict[str, int] = {tile: idx for idx, tile in enumerate(INDEX34_TO_TILE)}
TILES_TO_INDEX34['0s'] = TILES_TO_INDEX34['5s']
TILES_TO_INDEX34['0m'] = TILES_TO_INDEX34['5m']
TILES_TO_INDEX34['0p'] = TILES_TO_INDEX34['5p']

SANMA_INVALID_TILES = {f'{i}m' for i in (0, 2, 3, 4, 5, 6, 7, 8)}





