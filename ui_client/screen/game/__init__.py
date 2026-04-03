import logging
import tkinter as tk

from mjs_client.client import ClientPhase
from mjs_client.game.game import Game
from mjs_client.game.gamephase import GamePhase
from mjs_client.game.gamestate import GameState
from mjs_client.game.operation import AbstractOperation, AbstractCallOperation
from .assistant import GameAssistantFrame

from ...image import ROTATION_MATRICES, abs_anchor
from ...language import tr

from ..abstract import AbstractScreen

from .tile_group import CallSelectionGroup, HandTileGroup, DiscardTileGroup, DoraGroup
from .operation_buttons import OperationButtonGroup


class Liqibang:
    def __init__(self, canvas: tk.Canvas, center: tuple[int, int], size: tuple[int, int], radius: int, rotation: int):
        self.canvas = canvas
        self.center = center
        self.rotation = rotation
        self.size = ROTATION_MATRICES[rotation](*size)

        xc, yc = center
        dx, dy = self.size[0] // 2, self.size[1] // 2
        self.rect: tuple[int, int, int, int] = (xc - dx, yc - dy, xc + dx, yc + dy)
        self.circle_rect: tuple[int, int, int, int] = (xc - radius, yc - radius, xc + radius, yc + radius)

        self.rect_id = 0
        self.circle_id = 0
        self.created = False

    def draw(self, draw: bool):
        if draw and not self.created:
            self.rect_id = self.canvas.create_rectangle(self.rect, fill="white")
            self.circle_id = self.canvas.create_oval(self.circle_rect, fill="red", width=0)
            self.created = True
        elif not draw and self.created:
            self.canvas.delete(self.rect_id)
            self.canvas.delete(self.circle_id)
            self.created = False



class CallSelectionSubframe:
    def __init__(self, call_selection_group: CallSelectionGroup, rect_size: tuple[int, int]):
        self.group = call_selection_group
        self.canvas = self.group.canvas
        self.rect: tuple[int, int, int, int] = (self.group.origin[0], self.group.origin[1],
                                                self.group.origin[0] + rect_size[0], self.group.origin[1] + rect_size[1])
        self.rect_id: int = 0
        self.created: bool = False

    def draw(self, operation_list: list[AbstractCallOperation]):
        if not self.created:
            self.rect_id = self.canvas.create_rectangle(self.rect, fill="lightblue", width=0)
            self.group.set_operation_list(operation_list)
            self.group.redraw()
            self.created = True

    def clear(self):
        if self.created:
            self.canvas.delete(self.rect_id)
            self.group.set_operation_list([])
            self.group.redraw()
            self.created = True


class GameScreen(AbstractScreen):
    PHASE = ClientPhase.INGAME
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 800
    CANVAS_MID_X = CANVAS_WIDTH // 2
    CANVAS_MID_Y = CANVAS_HEIGHT // 2
    def __init__(self, parent, ui):
        super().__init__(parent, ui)

        self.game: Game = self.client.game
        self.game_state: GameState = self.client.game.action_handler.game_state

        self.canvas = tk.Canvas(self.frame, width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT)
        self.canvas.grid(row=0, column=0)

        self.canvas.create_rectangle(self.CANVAS_MID_X-120, self.CANVAS_MID_Y-120, self.CANVAS_MID_X+120, self.CANVAS_MID_Y+120,
                                     outline="black")

        self.operation_button_group = OperationButtonGroup(self, (648, 732), tk.SE, (64, 25))
        self.call_selection_subframe = CallSelectionSubframe(CallSelectionGroup(self.canvas, self.game_state, (200, 675), 0, 0.4,
                                                                                self.tile_bind_func),
                                                             (320, 50))

        self.hand_tile_groups: list[HandTileGroup] = []
        self.discard_groups: list[DiscardTileGroup] = []
        self.player_text: list[tk.Label] = []
        self.wind_text: list[tk.Label] = []
        self.liqibangs: list[Liqibang] = []
        for rotation in range(4):
            rot_matrix = ROTATION_MATRICES[rotation]
            # hand
            rel_x, rel_y = rot_matrix(-312, 332)
            self.hand_tile_groups.append(HandTileGroup(self.canvas, self.game_state, self.operation_button_group,
                                                       (self.CANVAS_MID_X+rel_x, self.CANVAS_MID_Y+rel_y),
                                                       rotation, 0.5, self.tile_bind_func))

            # player text
            new_label = tk.Label(self.canvas)
            self.player_text.append(new_label)
            self.canvas.create_window(self.CANVAS_MID_X + rel_x, self.CANVAS_MID_Y + rel_y,
                                      anchor=abs_anchor(rotation, tk.SW), window=new_label)

            # center (wind) text
            rel_x, rel_y = rot_matrix(-90, 110)
            new_label = tk.Label(self.canvas)
            self.wind_text.append(new_label)
            self.canvas.create_window(self.CANVAS_MID_X + rel_x, self.CANVAS_MID_Y + rel_y,
                                      anchor=abs_anchor(rotation, tk.SW), window=new_label)

            # discard
            rel_x, rel_y = rot_matrix(-120, 120)
            self.discard_groups.append(DiscardTileGroup(self.canvas, self.game_state,
                                                        (self.CANVAS_MID_X+rel_x, self.CANVAS_MID_Y+rel_y),
                                                        rotation, 0.5))
            # liqibang
            rel_x, rel_y = rot_matrix(0, 105)
            self.liqibangs.append(Liqibang(self.canvas, (self.CANVAS_MID_X+rel_x, self.CANVAS_MID_Y+rel_y),
                                           (130, 16), 3, rotation))

        self.label_chang = tk.Label(self.canvas)
        self.canvas.create_window(self.CANVAS_MID_X, self.CANVAS_MID_Y - 90, anchor=tk.N, window=self.label_chang)
        self.liqibang_changgong = Liqibang(self.canvas, (self.CANVAS_MID_X - 30, self.CANVAS_MID_Y - 20),
                                           (60, 8), 2, 1)
        self.label_changgong = tk.Label(self.canvas)
        self.canvas.create_window(self.CANVAS_MID_X, self.CANVAS_MID_Y - 20, anchor=tk.W, window=self.label_changgong)
        self.dora_group = DoraGroup(self.canvas, self.game_state,
                                    (self.CANVAS_MID_X - 60, self.CANVAS_MID_Y + 20), 0, 0.3)

        self.frame_round_result = tk.Frame(self.canvas, bg='lightblue')
        self.frame_round_result_id: int = 0
        self.label_round_result = tk.Label(self.frame_round_result)
        self.label_round_result.grid(row=1, column=1)
        self.labels_delta_scores: list[tk.Label] = [tk.Label(self.frame_round_result, bg='lightblue') for i in range(4)]
        self.labels_delta_scores[0].grid(row=2, column=1)
        self.labels_delta_scores[1].grid(row=1, column=2)
        self.labels_delta_scores[2].grid(row=0, column=1)
        self.labels_delta_scores[3].grid(row=1, column=0)
        self.button_confirm_round_result = tk.Button(self.frame_round_result, command=self.confirm_button_func)
        self.button_confirm_round_result.grid(row=2, column=2)
        self.round_results_displaying = False
        self.show_end_screen = False

        self.frame_for_assistant = tk.Frame(self.frame)
        self.frame_for_assistant.grid(row=0, column=1)
        self.assistant = GameAssistantFrame(self.frame_for_assistant, self)

        self.update_text()

    def update_text(self):
        self.assistant.update_text()

    def update(self):
        self.operation_button_group.update()
        self.call_selection_subframe.clear()
        for rotation in range(4):
            self.hand_tile_groups[rotation].redraw()
            self.discard_groups[rotation].redraw()
            self.update_label_text_and_liqi(rotation)
        self.label_chang.config(text=tr("game.round.{}".format(self.game_state.current_chang)).format(self.game_state.current_ju+1, self.game_state.current_benchang) + '\n' +
                                tr("game.remain").format(self.game_state.left_tile_count))
        self.liqibang_changgong.draw(True)
        self.label_changgong.config(text="x {}".format(self.game_state.liqibang))
        self.dora_group.redraw()
        #logging.info(f"GameScreen update: show_end_screen={self.show_end_screen}, phase={self.game_state.phase}")
        #logging.info(f"Round results label config: {self.label_round_result.config()}")
        if self.game_state.phase == GamePhase.BETWEEN_ROUNDS:
            if not self.show_end_screen:
                self.label_round_result.config(text=self.get_round_result_text())
                self.frame_round_result_id = self.canvas.create_window(self.CANVAS_MID_X, self.CANVAS_MID_Y, anchor=tk.CENTER, window=self.frame_round_result)
                for rotation in range(4):
                    seat = (self.game_state.my_seat + rotation) % 4
                    if seat >= self.game_state.player_count:
                        delta_score_text = ""
                    else:
                        delta_score_text = "{:+d}".format(self.game_state.round_result.delta_scores[seat])
                    self.labels_delta_scores[rotation].config(text=delta_score_text)
                self.button_confirm_round_result.config(text=tr("game.confirm"))
                self.round_results_displaying = True
                logging.info("Round result frame display")
        elif self.round_results_displaying:
            self.canvas.delete(self.frame_round_result_id)
            self.round_results_displaying = False
            logging.info("Round result frame destroyed")

    def get_round_result_text(self) -> str:
        lines = []
        for win_info in self.game_state.round_result.win:
            player_name = self.game.player_names[win_info.seat]
            if not player_name:
                player_name = tr("room.bot")
            lines.append(tr("game.win.tsumo" if win_info.tsumo else "game.win.ron").format(player_name))
            if win_info.yakuman:
                line_fmt = tr("game.win.yakuman_line")
                for yaku_id, value in win_info.yakus.items():
                    yaku_name = tr("game.win.yaku.{}".format(yaku_id))
                    lines.append(line_fmt.format(yaku_name))
                lines.append(tr("game.win.value_yakuman.{}".format(win_info.fan)).format(win_info.score))
            else:
                line_fmt = tr("game.win.yaku_line")
                for yaku_id, value in win_info.yakus.items():
                    yaku_name = tr("game.win.yaku.{}".format(yaku_id))
                    lines.append(line_fmt.format(yaku_name, value))
                lines.append(tr("game.win.value").format(win_info.fan, win_info.fu, win_info.score))
        return "\n".join(lines)

    def get_game_result_text(self) -> str:
        lines = []
        for rank, end_result in enumerate(self.game_state.game_result):
            lines.append(tr("game.result").format(rank+1, self.game.player_names[end_result.seat], end_result.point, end_result.score, end_result.pt))
        return "\n".join(lines)


    def update_label_text_and_liqi(self, rotation: int):
        seat = (self.game_state.my_seat + rotation) % 4
        if seat >= self.game_state.player_count:
            return
        wind_position = (seat - self.game_state.current_ju) % 4
        player_name = self.game.player_names[seat]
        if player_name == "":
            player_name = tr("room.bot")
        self.player_text[rotation].config(text=(player_name + "\n" + str(self.game_state.scores[seat])))
        self.wind_text[rotation].config(text=tr("game.wind.{}".format(wind_position)))
        self.liqibangs[rotation].draw(bool(self.game_state.player_liqis[seat]))

    def tile_bind_func(self, op: AbstractOperation, event: tk.Event):
        self.controller.game_put_operation(op)

    def put_operation(self, op: AbstractOperation):
        self.controller.game_put_operation(op)

    def confirm_button_func(self):
        logging.info(f"Confirm button: ended={self.game_state.ended}")
        if self.game_state.ended:
            if self.show_end_screen:
                self.controller.return_from_game()
            else:
                self.show_end_screen = True
                for rotation in range(4):
                    self.labels_delta_scores[rotation].config(text="")
                self.label_round_result.config(text=self.get_game_result_text())
        else:
            self.controller.game_confirm_new_round()

