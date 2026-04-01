import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ....language import tr
from ....scripts import PackageScriptManager, PackageWrapper, LoadPackageCode

from .. import SettingsSubframe


class ScriptsFrame(SettingsSubframe):
    def __init__(self, parent, ui):
        super().__init__(parent, ui)
        self.scripts_manager: PackageScriptManager = self.ui.scripts_manager

        self.scripts_label = tk.Label(self.parent)
        self.scripts_label.grid(row=0, column=0)

        self.scripts_treeview = ttk.Treeview(self.parent, columns=("script", "source"), show="headings")
        self.scripts_treeview.grid(row=0, column=1)
        self.iid_package_map: dict[str, PackageWrapper | None] = {}

        self.button_frame = tk.Frame(self.parent)
        self.button_frame.grid(row=1, column=1)

        self.script_add_button = tk.Button(self.button_frame, command=self.add_script)
        self.script_add_button.grid(row=0, column=0)

        self.script_remove_button = tk.Button(self.button_frame, command=self.remove_script)
        self.script_remove_button.grid(row=0, column=1)

        self.script_resync_button = tk.Button(self.button_frame, command=self.resync_script)
        self.script_resync_button.grid(row=0, column=2)


    def apply(self):
        pass

    def update_text(self):
        self.scripts_label.config(text=tr("settings.scripts.label"))

        self.scripts_treeview.heading("script", text=tr("settings.scripts.heading.script"))
        self.scripts_treeview.heading("source", text=tr("settings.scripts.heading.source"))

        self._reset_treeview()

        self.script_add_button.config(text=tr("settings.scripts.button.add"))
        self.script_remove_button.config(text=tr("settings.scripts.button.remove"))
        self.script_resync_button.config(text=tr("settings.scripts.button.resync"))

    def _add_package(self, package_wrapper):
        for script_wrapper in package_wrapper.scripts:
            iid = self.scripts_treeview.insert('', tk.END, values=(script_wrapper.get_name(), package_wrapper.get_name()))
            self.iid_package_map[iid] = package_wrapper

    def _reset_treeview(self):
        for item in self.scripts_treeview.get_children():
            self.scripts_treeview.delete(item)
        self.iid_package_map.clear()

        for package_wrapper in self.scripts_manager.packages.values():
            self._add_package(package_wrapper)

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
        package_to_remove: set[str] = set()          # names
        package_to_remove_nicknames: list[str] = []  # nicknames get by get_name()
        iid_to_remove: set[str] = set()
        for selected_item_iid in self.scripts_treeview.selection():
            if selected_item_iid in self.iid_package_map:
                package_wrapper = self.iid_package_map[selected_item_iid]
                if package_wrapper.is_default:
                    messagebox.showinfo(tr("settings.scripts.dialog.title_info"), tr("settings.scripts.dialog.remove_default"))
                    return
                package_to_remove.add(package_wrapper.name)
                package_to_remove_nicknames.append(package_wrapper.get_name())
            else:
                self.iid_package_map[selected_item_iid] = None
                logging.error(f"Selected item {selected_item_iid} not in iid_package_map")
            iid_to_remove.add(selected_item_iid)

        if not package_to_remove:
            return

        dialog_text = tr("settings.scripts.dialog.remove").format(len(package_to_remove)) + '\n'.join(package_to_remove_nicknames)
        ok = messagebox.askokcancel(tr("settings.scripts.dialog.title_warning"), dialog_text)
        if ok:
            for package_name in package_to_remove:
                self.scripts_manager.remove_script(package_name)
            for iid in iid_to_remove:
                self.iid_package_map.pop(iid)
                self.scripts_treeview.delete(iid)

    def resync_script(self):
        self.scripts_manager.sync_scripts_folder()
        self._reset_treeview()
