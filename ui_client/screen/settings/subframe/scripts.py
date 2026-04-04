import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Any

from ...treeview_list import TreeviewList, TreeviewColumn
from ....language import tr
from ....scripts import PackageScriptManager, PackageWrapper, LoadPackageCode, ScriptClassWrapper

from .. import SettingsSubframe


class ScriptsTreeviewList(TreeviewList):
    COLUMNS = (TreeviewColumn("script", lambda item: item.get_name()),
               TreeviewColumn("source", lambda item: item.package_wrapper.get_name()))

    def __init__(self, parent, *, tag_seeker: Callable[[Any], str] = None, **kwargs):
        super().__init__(parent, self.COLUMNS, tag_seeker=tag_seeker, **kwargs)

    def reset_to(self, scripts_manager: PackageScriptManager):
        self.reset([s for package_wrapper in scripts_manager.packages.values()
                    for s in package_wrapper.scripts.values()])

    def update_heading(self):
        self.heading("script", text=tr("settings.scripts.heading.script"))
        self.heading("source", text=tr("settings.scripts.heading.source"))


class ScriptsFrame(SettingsSubframe):
    def __init__(self, parent, screen):
        super().__init__(parent, screen)
        self.scripts_manager: PackageScriptManager = self.ui.scripts_manager

        self.scripts_label = tk.Label(self.parent)
        self.scripts_label.grid(row=0, column=0)

        self.scripts_treeview_list = ScriptsTreeviewList(self.parent)
        self.scripts_treeview_list.grid(row=0, column=1)

        self.button_frame = tk.Frame(self.parent)
        self.button_frame.grid(row=1, column=1)

        self.script_add_button = tk.Button(self.button_frame, command=self.add_script)
        self.script_add_button.grid(row=0, column=0)

        self.script_remove_button = tk.Button(self.button_frame, command=self.remove_script)
        self.script_remove_button.grid(row=0, column=1)

        self.script_resync_button = tk.Button(self.button_frame, command=self.resync_script)
        self.script_resync_button.grid(row=0, column=2)

        self.scripts_treeview_list.reset_to(self.scripts_manager)


    def apply(self):
        pass

    def update_text(self):
        self.scripts_label.config(text=tr("settings.scripts.label"))

        self.scripts_treeview_list.update_heading()

        self.script_add_button.config(text=tr("settings.scripts.button.add"))
        self.script_remove_button.config(text=tr("settings.scripts.button.remove"))
        self.script_resync_button.config(text=tr("settings.scripts.button.resync"))

    def _add_package(self, package_wrapper):
        for script_wrapper in package_wrapper.scripts.values():
            self.scripts_treeview_list.append(script_wrapper)

    def add_script(self, folder_path=None):
        if folder_path is None:
            folder_path = filedialog.askdirectory()
            if not folder_path:
                return

        load_res, package_wrapper = self.scripts_manager.copy_folder_and_load(folder_path)
        if load_res.code == LoadPackageCode.SUCCESS:
            self._add_package(package_wrapper)
            return

        dialog_text = tr("settings.scripts.dialog.load.{}".format(load_res.code))
        if load_res.code == LoadPackageCode.PACKAGE_FOLDER_EXISTS:
            overwrite = messagebox.askokcancel(tr("settings.scripts.dialog.title_warning"), dialog_text)
            if overwrite:
                self.add_script(folder_path)
        else:
            messagebox.showerror(tr("settings.scripts.dialog.load.title_error"), dialog_text)

    def remove_script(self):
        target_packages_names: set[str] = set()
        target_packages_display_names: set[str] = set()

        selected_item: ScriptClassWrapper
        for selected_item in self.scripts_treeview_list.get_selected_items():
            if selected_item.package_wrapper.is_default:
                messagebox.showinfo(tr("settings.scripts.dialog.title_info"),
                                    tr("settings.scripts.dialog.remove_default"))
                return
            target_packages_names.add(selected_item.package_wrapper.name)
            target_packages_display_names.add(selected_item.package_wrapper.get_name())

        if not target_packages_names:
            return

        dialog_text = tr("settings.scripts.dialog.remove").format(len(target_packages_names)) \
                       + '\n'.join(target_packages_display_names)
        ok = messagebox.askokcancel(tr("settings.scripts.dialog.title_warning"), dialog_text)
        if not ok:
            return

        for package_name in target_packages_names:
            self.scripts_manager.remove_script(package_name)
        self.scripts_treeview_list.removes(filter_func=lambda s: s.package_wrapper.name in target_packages_names)

    def resync_script(self):
        self.scripts_manager.sync_scripts_folder()
