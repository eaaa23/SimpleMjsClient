import logging
import tkinter as tk
from tkinter import messagebox
from functools import partial

from .scripts import ScriptsTreeviewList
from ....config import config, AutoBotInfo, AutoBotItemInfo
from ....language import tr, get_available_languages, get_language_from_name

from ... import AbstractScreen
from ...treeview_list import TreeviewList, TreeviewColumn

from .. import SettingsSubframe
from ....scripts import ScriptClassWrapper, PackageScriptManager


class BotConfigScreen(AbstractScreen):
    def __init__(self, parent, ui, autobot_info: AutoBotInfo | None):
        super().__init__(parent, ui)
        self.scripts_manager: PackageScriptManager = self.ui.scripts_manager

        if autobot_info is None:
            self.is_new_bot = True
            self.autobot_info = AutoBotInfo()
        else:
            self.is_new_bot = False
            self.autobot_info = autobot_info

        self.modified = False

        self.bot_frame = tk.Frame(self.frame)
        self.bot_frame.grid(row=0, column=0, padx=10)

        self.script_select_frame = tk.Frame(self.frame)
        self.script_select_frame.grid(row=0, column=1)

        self.bot_name_label = tk.Label(self.bot_frame)
        self.bot_name_label.grid(row=0, column=0)

        self.bot_name_var = tk.StringVar()
        self.bot_name_entry = tk.Entry(self.bot_frame, textvariable=self.bot_name_var)
        self.bot_name_entry.grid(row=0, column=1, sticky="w")

        self.bot_items_label = tk.Label(self.bot_frame)
        self.bot_items_label.grid(row=1, column=0, sticky="nw")

        self.bot_items_treeview_list = TreeviewList(self.bot_frame,
                                                    columns=(TreeviewColumn("package", self.scripts_manager.get_package_name),
                                                             TreeviewColumn("class", self.scripts_manager.get_class_name),
                                                             TreeviewColumn("threshold", lambda autobot_item_info: "{:.2f}".format(autobot_item_info.threshold))),
                                                    tag_seeker=lambda autobot_item_info: () if self.scripts_manager.check_bot_item_info_valid(autobot_item_info) else "red",
                                                    selectmode=tk.BROWSE)
        self.bot_items_treeview_list.tag_configure("red", foreground="red")
        self.bot_items_treeview_list.grid(row=1, column=1)

        self.button_frame = tk.Frame(self.bot_frame)
        self.button_frame.grid(row=2, column=1)

        self.remove_item_button = tk.Button(self.button_frame, command=self.remove_item_button_clicked)
        self.remove_item_button.grid(row=0, column=0)

        self.uplift_item_button = tk.Button(self.button_frame, command=self.uplift_item_button_clicked)
        self.uplift_item_button.grid(row=0, column=1)

        self.downgrade_item_button = tk.Button(self.button_frame, command=self.downgrade_item_button_clicked)
        self.downgrade_item_button.grid(row=0, column=2)

        self.threshold_frame = tk.Frame(self.bot_frame)
        self.threshold_frame.grid(row=3, column=1)

        self.threshold_label = tk.Label(self.threshold_frame)
        self.threshold_label.grid(row=0, column=0)

        self.var_threshold = tk.StringVar()
        self.threshold_entry = tk.Entry(self.threshold_frame, textvariable=self.var_threshold)
        self.threshold_entry.grid(row=0, column=1)
        self.threshold_entry.bind("<Return>", lambda e: self.threshold_set_button_clicked())
        self.threshold_entry.bind("<Up>", lambda e: self._move_selected(-1))
        self.threshold_entry.bind("<Down>", lambda e: self._move_selected(1))

        self.threshold_set_button = tk.Button(self.threshold_frame, command=self.threshold_set_button_clicked)
        self.threshold_set_button.grid(row=0, column=2)

        self.script_select_label = tk.Label(self.script_select_frame)
        self.script_select_label.grid(row=0, column=0, sticky='n')

        self.script_select_treeview_list = ScriptsTreeviewList(self.script_select_frame, selectmode=tk.BROWSE)
        self.script_select_treeview_list.grid(row=1, column=0)

        self.script_add_button = tk.Button(self.script_select_frame, command=self.script_add_button_clicked)
        self.script_add_button.grid(row=2, column=0)

        self.instruction_label = tk.Label(self.frame)
        self.instruction_label.grid(row=1, column=0)

        self.save_button = tk.Button(self.frame, command=self.save_and_quit)
        self.save_button.grid(row=2, column=0, sticky="se")

        self.script_select_treeview_list.reset_to(self.scripts_manager)
        self.bot_name_var.set(self.autobot_info.name)
        self.bot_items_treeview_list.reset(self.autobot_info.items)
        self.update_text()

    def update_text(self):
        self.parent.title(tr("settings.autobot.config.title"))

        self.bot_name_label.config(text=tr("settings.autobot.config.label.name"))

        self.bot_items_label.config(text=tr("settings.autobot.config.label.scripts"))

        self.bot_items_treeview_list.heading("package", text=tr("settings.autobot.config.heading.package"))
        self.bot_items_treeview_list.heading("class", text=tr("settings.autobot.config.heading.class"))
        self.bot_items_treeview_list.heading("threshold", text=tr("settings.autobot.config.heading.threshold"))

        self.remove_item_button.config(text=tr("settings.autobot.config.remove"))
        self.uplift_item_button.config(text=tr("settings.autobot.config.uplift"))
        self.downgrade_item_button.config(text=tr("settings.autobot.config.downgrade"))

        self.threshold_label.config(text=tr("settings.autobot.config.label.set_threshold"))
        self.threshold_set_button.config(text=tr("settings.autobot.config.set_threshold"))

        self.script_select_label.config(text=tr("settings.autobot.config.label.select"))
        self.script_select_treeview_list.update_heading()
        self.script_add_button.config(text=tr("settings.autobot.config.add"))

        self.instruction_label.config(text=tr("settings.autobot.config.instruction"))

        self.save_button.config(text=tr("settings.autobot.config.save"))

    def save(self) -> bool:
        bot_name = self.bot_name_var.get()
        if not bot_name:
            messagebox.showerror(tr("settings.autobot.config.dialog.title_error"),
                                 tr("settings.autobot.config.dialog.empty_name"))
            return False
        for bot_info in config.autobots:
            if bot_info.name == bot_name and bot_info is not self.autobot_info:
                messagebox.showerror(tr("settings.autobot.config.dialog.title_error"),
                                     tr("settings.autobot.config.dialog.name_conflict"))
                return False

        bot_items = self.bot_items_treeview_list.get_items()
        if not bot_items:
            messagebox.showerror(tr("settings.autobot.config.dialog.title_error"),
                                 tr("settings.autobot.config.dialog.no_items"))
            return False

        self.autobot_info.name = bot_name
        self.autobot_info.items = bot_items
        if self.is_new_bot:
            config.autobots.append(self.autobot_info)
            self.is_new_bot = False   # not necessary now but maybe in the future
        config.save()
        return True

    def save_and_quit(self):
        if self.save():
            self.close()

    def on_user_shut_window(self) -> bool:
        if self.modified:
            res = messagebox.askyesnocancel(tr("settings.autobot.config.dialog.title_warning"),
                                        tr("settings.autobot.config.dialog.save"))
        else:
            # Not modified, res should be False, but it's better to set it to True
            # Prevent corner case when the list is changed but self.modified == False
            # In this case it's better to save than not save.
            # However, it's better to let user quit if this is a new bot
            res = not self.is_new_bot

        if res is True:
            return self.save()
        elif res is False:
            return True
        else: # res is None
            return False

    def script_add_button_clicked(self):
        selected_items = self.script_select_treeview_list.get_selected_items()
        if not selected_items:
            return
        selected_class_wrapper: ScriptClassWrapper = selected_items[0]
        self.bot_items_treeview_list.append(selected_class_wrapper.to_item_info())
        self.bot_items_treeview_list.selection_set(self.bot_items_treeview_list.length()-1)
        self.modified = True

    def remove_item_button_clicked(self):
        self.bot_items_treeview_list.remove_selected()
        self.modified = True

    def _move_selected(self, offset: int):
        if selected_indexes := self.bot_items_treeview_list.get_selected_indexes():
            target_idx = selected_indexes[0] + offset
            if 0 <= target_idx < self.bot_items_treeview_list.length():
                self.bot_items_treeview_list.selection_set(target_idx)

    def _change_priority(self, offset: int):
        selected_indexes = self.bot_items_treeview_list.get_selected_indexes()
        if not selected_indexes:
            return
        selected_idx = selected_indexes[0]
        swap_idx = selected_idx + offset
        if swap_idx < 0 or swap_idx >= self.bot_items_treeview_list.length():
            return
        self.bot_items_treeview_list.swap(selected_idx, swap_idx)
        self.bot_items_treeview_list.selection_set(swap_idx)
        self.modified = True

    def uplift_item_button_clicked(self):
        self._change_priority(-1)

    def downgrade_item_button_clicked(self):
        self._change_priority(1)

    def threshold_set_button_clicked(self):
        value_str = self.var_threshold.get()
        try:
            value_float = float(value_str)
            if value_float > 1.0 or value_float < 0.0:
                raise ValueError
        except ValueError:
            messagebox.showerror(tr("settings.autobot.config.dialog.title_error"), tr("settings.autobot.config.dialog.threshold_invalid"))
            return
        selected_enumeration = self.bot_items_treeview_list.get_selected_enumeration()
        if not selected_enumeration:
            return
        selected_index, selected_item = selected_enumeration[0]
        selected_item.threshold = value_float
        self.bot_items_treeview_list.refresh_display(selected_index)
        self.modified = True


class AutoBotSettingsFrame(SettingsSubframe):
    def __init__(self, parent, screen):
        super().__init__(parent, screen)

        self.auto_bot_config_label = tk.Label(self.parent)
        self.auto_bot_config_label.grid(row=0, column=0)

        self.bot_display_frame = tk.Frame(self.parent)
        self.bot_display_frame.grid(row=0, column=1)

        self.bots_treeview_list = TreeviewList(self.bot_display_frame,
                                               columns=(TreeviewColumn("name", lambda autobot_info: autobot_info.name),
                                                        TreeviewColumn("default", lambda autobot_info: tr(
                                                            "settings.autobot.display.yes") if autobot_info.name == config.default_autobot_name else "")),
                                               selectmode=tk.BROWSE)
        self.bots_treeview_list.grid(row=0, column=0, sticky="w")

        self.button_frame = tk.Frame(self.bot_display_frame)
        self.button_frame.grid(row=1, column=0)

        self.bot_add_button = tk.Button(self.button_frame, command=self.on_add_button_click)
        self.bot_add_button.grid(row=0, column=0)

        self.bot_config_button = tk.Button(self.button_frame, command=self.on_config_button_click)
        self.bot_config_button.grid(row=0, column=1)

        self.bot_remove_button = tk.Button(self.button_frame, command=self.on_remove_button_click)
        self.bot_remove_button.grid(row=0, column=2)

        self.set_default_button = tk.Button(self.button_frame, command=self.on_set_default_button_click)
        self.set_default_button.grid(row=1, column=0)

        self.cancel_default_button = tk.Button(self.button_frame, command=self.on_cancel_default_button_click)
        self.cancel_default_button.grid(row=1, column=1)

        self.update_text()
        self.update()

    def update_text(self):
        self.auto_bot_config_label.config(text=tr("settings.autobot.label"))

        self.bots_treeview_list.heading("name", text=tr("settings.autobot.display.bot_name"))
        self.bots_treeview_list.heading("default", text=tr("settings.autobot.display.default"))

        self.bot_add_button.config(text=tr("settings.autobot.display.add"))
        self.bot_config_button.config(text=tr("settings.autobot.display.config"))
        self.bot_remove_button.config(text=tr("settings.autobot.display.remove"))
        self.set_default_button.config(text=tr("settings.autobot.display.set_default"))
        self.cancel_default_button.config(text=tr("settings.autobot.display.cancel_default"))

    def update(self):
        self.bots_treeview_list.reset(config.autobots)

    def on_add_button_click(self):
        self.screen.new_window(BotConfigScreen, autobot_info=None)

    def on_config_button_click(self):
        selected_items = self.bots_treeview_list.get_selected_items()
        if selected_items:
            self.screen.new_window(BotConfigScreen, autobot_info=selected_items[0])

    def on_remove_button_click(self):
        selected_indexes = self.bots_treeview_list.get_selected_indexes()
        if selected_indexes:
            del config.autobots[selected_indexes[0]]
            self.bots_treeview_list.remove_selected()

    def on_set_default_button_click(self):
        selected_items = self.bots_treeview_list.get_selected_items()
        if selected_items:
            config.default_autobot_name = selected_items[0].name
            config.save()
            self.bots_treeview_list.refresh_display()

    def on_cancel_default_button_click(self):
        selected_items = self.bots_treeview_list.get_selected_items()
        if selected_items:
            selected_item: AutoBotInfo = selected_items[0]
            if selected_item.name == config.default_autobot_name:
                config.default_autobot_name = ""
                config.save()
                self.bots_treeview_list.refresh_display()

    def apply(self):
        pass