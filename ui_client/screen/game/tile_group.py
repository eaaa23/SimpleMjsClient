from abc import abstractmethod
from dataclasses import dataclass
from functools import partial
import tkinter as tk
from typing import Callable, Any

from PIL import ImageTk

from mjs_client.const import OperationType
from mjs_client.game.operation import AbstractOperation, PlayTile, Liqi, AbstractCallOperation
from mjs_client.game.operation_container import OperationContainer
from mjs_client.game.phases import GamePhase
from mjs_client.game.gamestate import GameState, Open, OpenType, Discard

from ...image import abs_anchor, Img, ROTATION_MATRICES

from .operation_buttons import OperationButtonGroup


@dataclass
class TileInfo:
    tile: str
    rel_rotation: int = 0
    alpha: float = 1.0
    spacing: float = -1.0
    addgang: bool = False
    bind_operation: AbstractOperation | None = None


class AbstractTileGroup:
    def __init__(self, canvas: tk.Canvas, game_state: GameState,
                 origin: tuple[int, int], rotation: int = 0, scale: float = 1,
                 bind_function: Callable[[AbstractOperation, tk.Event], Any] = None):
        self.canvas = canvas
        self.game_state = game_state
        self.origin = origin
        self.last_image_id: list[int] = []
        self.image_cache: list[ImageTk.PhotoImage] = []     # Prevent GC
        self.rotation = rotation
        self._anchor = abs_anchor(rotation, tk.SW)
        self.scale = scale
        self.bind_function = bind_function
        test_img = Img("00.png", scale=self.scale)
        self.img_width = test_img.width()
        self.img_height = test_img.height()
        self.seat = (self.game_state.my_seat + self.rotation) % 4

    def update_state(self):
        pass

    @abstractmethod
    def grid_tile(self) -> list[list[TileInfo]]:
        pass

    def redraw(self):
        for id_ in self.last_image_id:
            self.canvas.delete(id_)
        self.last_image_id.clear()
        self.image_cache.clear()

        self.update_state()

        for row_idx, row in enumerate(self.grid_tile()):
            i = 0
            for info in row:
                i_increment = ROTATION_MATRICES[info.rel_rotation](self.img_width, self.img_height)[0]
                if info.spacing > 0:
                    i_increment = int(i_increment * info.spacing)
                else:
                    image = Img("{}.png".format(info.tile), rotation=self.rotation+info.rel_rotation,
                                scale=self.scale, alpha=info.alpha)
                    self.image_cache.append(image)

                    j = self.img_height * (row_idx + 1) - info.addgang * self.img_width
                    rel_x, rel_y = ROTATION_MATRICES[self.rotation](i - info.addgang * self.img_height, j)
                    self.last_image_id.append(self.canvas.create_image(self.origin[0] + rel_x, self.origin[1] + rel_y,
                                                                       image=image, anchor=self._anchor))
                    if info.bind_operation is not None and self.bind_function is not None:
                        self.canvas.tag_bind(self.last_image_id[-1], "<Button-1>", partial(self.bind_function, info.bind_operation))
                if not info.addgang:
                    i += i_increment


class HandTileGroup(AbstractTileGroup):
    """
    Includes open tiles.
    """
    def __init__(self, canvas: tk.Canvas, game_state: GameState, operation_button_group: OperationButtonGroup,
                 possible_operations: OperationContainer,
                 origin: tuple[int, int], rotation: int = 0, scale: float = 1,
                 bind_function: Callable[[AbstractOperation, tk.Event], Any] = None):
        super().__init__(canvas, game_state, origin, rotation, scale, bind_function)
        self.operation_button_group = operation_button_group
        self.possible_operations = possible_operations

        self.hand_tiles: list[str] = []
        self.opens: list[Open] = []
        self.peis: int = 0
        self.last_tile_do_spacing: bool = False
        self.liqi_pressed: bool = False

    def update_state(self):
        self.opens = reversed(self.game_state.player_opens[self.seat])
        self.peis = len(self.game_state.player_peis[self.seat])
        self.liqi_pressed = self.operation_button_group.liqi_pressed

        if self.game_state.phase == GamePhase.IN_PROGRESS:
            self.last_tile_do_spacing = self.game_state.last_operation_is_deal
            if self.rotation == 0:
                self.hand_tiles = self.game_state.my_hand
                return
        elif self.game_state.phase == GamePhase.BETWEEN_ROUNDS:
            for shown_hand in self.game_state.round_result.shown_hands:
                if self.seat == shown_hand.seat:
                    self.last_tile_do_spacing = True
                    self.hand_tiles = shown_hand.hand_tiles
                    return
        self.hand_tiles = ["00"] * self.game_state.player_hand_size[self.seat]

    def grid_tile(self) -> list[list[TileInfo]]:
        retval_0 = [self._get_hand_tile_info(tile) for tile in self.hand_tiles]
        if len(self.hand_tiles) % 3 == 2:
            if self.last_tile_do_spacing:
                retval_0.insert(-1, TileInfo(tile="", spacing=0.5))
                if retval_0[-1].bind_operation is not None:
                    retval_0[-1].bind_operation.is_moqie = True
            else:
                retval_0.append(TileInfo(tile="", spacing=0.5))
        else:  # == 1:
            retval_0.append(TileInfo(tile="", spacing=1.0))
            retval_0.append(TileInfo(tile="", spacing=0.5))

        if self.opens or self.peis:
            retval_0.append(TileInfo(tile="", spacing=0.5))
            retval_0.extend([TileInfo(tile="4z")] * self.peis)
            for open_ in self.opens:
                if open_.type == OpenType.ANGANG:
                    tile_hide = TileInfo(tile="00")
                    tile_show = TileInfo(tile=open_.tiles_self[0])
                    retval_0.extend([tile_hide, tile_show, tile_show, tile_hide])
                elif open_.type in (OpenType.CHI, OpenType.PONG, OpenType.MINGGANG, OpenType.ADDGANG):
                    tiles_self = open_.tiles_self[:-1] if open_.type == OpenType.ADDGANG else open_.tiles_self
                    new_tile_infos = [TileInfo(tile=tile) for tile in tiles_self]
                    insert_idx = (len(tiles_self), 1, 0)[open_.direction-1]
                    new_tile_infos.insert(insert_idx, TileInfo(tile=open_.tile_from_other, rel_rotation=1))
                    if open_.type == OpenType.ADDGANG:
                        new_tile_infos.insert(insert_idx+1, TileInfo(tile=open_.tiles_self[-1], rel_rotation=1, addgang=True))
                    retval_0.extend(new_tile_infos)
        return [retval_0]

    def _get_hand_tile_info(self, tile: str) -> TileInfo:
        # logging.info(f"In _get_hand_tile_info: {self.liqi_pressed}")
        if self.rotation != 0:
            return TileInfo(tile=tile)
        if self.liqi_pressed:
            if tile in (op.tile for op in self.possible_operations[OperationType.LIQI]):
                alpha = 1.0
            else:
                alpha = 0.3
            return TileInfo(tile=tile, bind_operation=Liqi(tile=tile, is_moqie=False), alpha=alpha)
        return TileInfo(tile=tile, bind_operation=PlayTile(tile=tile, is_moqie=False))


class TestHandTileGroup(HandTileGroup):
    """Debugging only"""
    def update_state(self):
        self.hand_tiles = ["0s"]
        self.opens = [Open(type=OpenType.ADDGANG, tiles_self=["5s", "5s", "0s"], direction=1, tile_from_other="5s") for i in range(4)]


class DiscardTileGroup(AbstractTileGroup):
    CHANGEROWS = (0, 6, 12)

    def __init__(self, canvas: tk.Canvas, game_state: GameState,
                 origin: tuple[int, int], rotation: int = 0, scale: float = 1):
        super().__init__(canvas, game_state, origin, rotation, scale)
        self.discards: list[Discard] = []

    def update_state(self):
        self.discards = self.game_state.player_discards[self.seat]

    def grid_tile(self) -> list[list[TileInfo]]:
        retval = []
        current_row = []
        for i, discard in enumerate(self.discards):
            if i in self.CHANGEROWS:
                current_row = []
                retval.append(current_row)
            current_row.append(TileInfo(tile=discard.tile, rel_rotation=int(discard.is_liqi),
                                        alpha=0.5 if discard.called else 1.0))
        return retval


class DoraGroup(AbstractTileGroup):
    def __init__(self, canvas: tk.Canvas, game_state: GameState,
                 origin: tuple[int, int], rotation: int = 0, scale: float = 1):
        super().__init__(canvas, game_state, origin, rotation, scale)
        self.doras = []

    def update_state(self):
        self.doras = self.game_state.doras.copy()
        self.doras.extend(["00"] * (5 - len(self.doras)))

    def grid_tile(self) -> list[list[TileInfo]]:
        return [[TileInfo(tile) for tile in self.doras]]


class CallSelectionGroup(AbstractTileGroup):
    def __init__(self, canvas: tk.Canvas, game_state: GameState,
                 origin: tuple[int, int], rotation: int = 0, scale: float = 1,
                 bind_function: Callable[[AbstractOperation, tk.Event], Any] = None):
        super().__init__(canvas, game_state, origin, rotation, scale, bind_function)
        self.operation_list: list[AbstractCallOperation] = []

    def set_operation_list(self, operation_list: list[AbstractCallOperation]):
        self.operation_list = operation_list.copy()

    def grid_tile(self) -> list[list[TileInfo]]:
        retval_0 = []
        for operation in self.operation_list:
            for combination_tile in operation.combination:
                retval_0.append(TileInfo(tile=combination_tile, bind_operation=operation))
            retval_0.append(TileInfo(tile="", spacing=1.0))
        return [retval_0]
