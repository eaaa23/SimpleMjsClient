import logging
import tkinter as tk
from typing import Literal

from mjs_client.const import OperationType
from mjs_client.game.gamestate import GameState
from mjs_client.game.operation import AbstractOperation
from mjs_client.game.operation_container import OperationContainer

from ...language import tr


class AbstractOperationButton:
    code: int
    sort_index: int = -1
    text_key: str = ""
    def __init__(self, button_group, operation_list: list[AbstractOperation | None]):
        self.group: OperationButtonGroup = button_group
        self.operation_list = operation_list
        self.button = tk.Button(self.group.canvas, text=tr(self.text_key), command=self.on_click)
        self.button_id: int = -1

    def hide(self):
        self.group.canvas.delete(self.button_id)

    def show(self, x, y):
        self.button_id = self.group.canvas.create_window(x, y, anchor=self.group.anchor, window=self.button)

    def on_click(self):
        self.group.screen.put_operation(self.operation_list[0])


class AbstractCallButton(AbstractOperationButton):
    def on_click(self):
        if len(self.operation_list) == 1:
            self.group.screen.put_operation(self.operation_list[0])
        else:
            self.group.screen.call_selection_subframe.draw(self.operation_list)


class ChiButton(AbstractCallButton):
    code = OperationType.CHI
    sort_index = 4
    text_key = "game.operation.chi"

class PongButton(AbstractCallButton):
    code = OperationType.PONG
    sort_index = 3
    text_key = "game.operation.pong"

class MingGangButton(AbstractCallButton):
    code = OperationType.MINGGANG
    sort_index = 5
    text_key = "game.operation.minggang"

class AnGangButton(AbstractCallButton):
    code = OperationType.ANGANG
    sort_index = 7
    text_key = "game.operation.angang"

class AddGangButton(AbstractCallButton):
    code = OperationType.ADDGANG
    sort_index = 6
    text_key = "game.operation.addgang"


class TsumoButton(AbstractOperationButton):
    code = OperationType.TSUMO
    sort_index = 2
    text_key = "game.operation.tsumo"


class RonButton(AbstractOperationButton):
    code = OperationType.RON
    sort_index = 1
    text_key = "game.operation.ron"


class PeiButton(AbstractOperationButton):
    code = OperationType.BABEI
    sort_index = 10
    text_key = "game.operation.pei"



class LiqiButton(AbstractOperationButton):
    code = OperationType.LIQI
    sort_index = 100
    text_key = "game.operation.liqi"
    def __init__(self, button_group, operation_list):
        super().__init__(button_group, operation_list)

    def on_click(self):
        self.group.liqi_pressed = not self.group.liqi_pressed
        #self.button.config(bg="#808080" if self.group.liqi_pressed else "#FFFFFF")
        self.group.screen.hand_tile_groups[0].redraw()

    def hide(self):
        super().hide()
        self.group.liqi_pressed = False


class CancelButton(AbstractOperationButton):
    code = -1
    sort_index = 0
    text_key = "game.operation.cancel"

    def on_click(self):
        if self.operation_list[0] is not None:
            self.group.screen.put_operation(self.operation_list[0])


# Without CancelButton
OPERATION_BUTTON_CLASSES = [ChiButton, PongButton, MingGangButton, AnGangButton, AddGangButton,
                            TsumoButton, RonButton, PeiButton, LiqiButton]


class OperationButtonGroup:
    def __init__(self, game_screen, origin: tuple[int, int], anchor: Literal[tk.NW, tk.NE, tk.SW, tk.SE],
                 button_size: tuple[int, int]):
        self.screen = game_screen
        self.canvas: tk.Canvas = game_screen.canvas
        self.origin = origin
        self.anchor = anchor
        self.row_flip = 1 if anchor in (tk.NW, tk.NE) else -1
        self.col_flip = 1 if anchor in (tk.NW, tk.SW) else -1
        self.button_size = button_size
        self.game_state: GameState = game_screen.game_state
        self.possible_operations: OperationContainer = game_screen.possible_operations
        self._buttons: dict[int, AbstractOperationButton] = {cls.code: cls(self, []) for cls in OPERATION_BUTTON_CLASSES}
        self._cancel_button = CancelButton(self, [None])
        self.active_buttons: list[AbstractOperationButton] = []
        self.liqi_pressed: bool = False

    def update(self):
        self.clear_buttons()
        cancel_button_op = None
        logging.info(f"OperationButtonGroup update: {self.possible_operations}")
        for code, operations in self.possible_operations.items():
            if code in self._buttons:
                if hasattr(operations[-1], "cancel_operation") and operations[-1].cancel_operation:
                    cancel_button_op = operations[-1]
                    oplist_for_button = operations[:-1]
                else:
                    oplist_for_button = operations
                self._buttons[code].operation_list = oplist_for_button
                self.active_buttons.append(self._buttons[code])
        if cancel_button_op:
            self._cancel_button.operation_list = [cancel_button_op]
            self.active_buttons.append(self._cancel_button)

        logging.info(f"OperationButtonGroup active_buttons: {self.active_buttons}")
        self.show_buttons()


    def clear_buttons(self):
        for active_button in self.active_buttons:
            active_button.hide()
        self.active_buttons.clear()

    def show_buttons(self):
        self.active_buttons.sort(key=lambda button: button.sort_index)
        for i, active_button in enumerate(self.active_buttons):
            x = self.origin[0] + self.col_flip * self.button_size[0] * (i % 2)
            y = self.origin[1] + self.row_flip * self.button_size[1] * (i // 2)
            active_button.show(x, y)







