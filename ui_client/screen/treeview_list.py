from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import TypeVar, Any, Sequence, Callable, Literal, Iterable


@dataclass
class TreeviewRow:
    iid: str
    item: Any


@dataclass
class TreeviewColumn:
    name: str
    mapping_to_display: Callable[[Any], str]


class TreeviewList:
    def __init__(self, parent: tk.Misc, columns: Sequence[TreeviewColumn],
                 *, tag_seeker: Callable[[Any], str] = None, **kwargs):
        self.parent = parent
        self.columns = columns
        self.tag_seeker = (lambda item: ()) if tag_seeker is None else tag_seeker
        self.rows: list[TreeviewRow] = []
        self.treeview = ttk.Treeview(parent, columns=[c.name for c in columns], show="headings", **kwargs)

    def _get_display_strings(self, value: Any) -> tuple[str, ...]:
        return tuple(column.mapping_to_display(value) for column in self.columns)

    def length(self) -> int:
        return len(self.rows)

    def insert(self, idx: int | Literal["end"], item: Any):
        if idx == tk.END:
            idx = len(self.rows)

        display_strings = self._get_display_strings(item)

        iid = self.treeview.insert('', idx, values=display_strings, tags=self.tag_seeker(item))

        self.rows.insert(idx, TreeviewRow(iid, item))

    def append(self, item: Any):
        self.insert(tk.END, item)

    def set(self, idx: int, item: Any):
        self.rows[idx].item = item
        self.refresh_display(idx)

    def swap(self, idx1: int, idx2: int):
        item1 = self.get(idx1)
        item2 = self.get(idx2)
        self.set(idx1, item2)
        self.set(idx2, item1)

    def get(self, idx: int) -> Any:
        return self.rows[idx].item

    def get_items(self) -> list[Any]:
        return [row.item for row in self.rows]

    def get_selected_items(self) -> list[Any]:
        return [row.item for row in self.rows if row.iid in set(self.treeview.selection())]

    def get_selected_indexes(self) -> list[int]:
        return [idx for idx, row in enumerate(self.rows) if row.iid in set(self.treeview.selection())]

    def get_selected_enumeration(self) -> list[tuple[int, Any]]:
        return [(idx, row.item) for idx, row in enumerate(self.rows) if row.iid in set(self.treeview.selection())]

    def refresh_display(self, *indexes: int):
        if not indexes:
            indexes = range(len(self.rows))
        for idx in indexes:
            iid = self.rows[idx].iid
            item = self.rows[idx].item
            for column in self.columns:
                self.treeview.set(iid, column.name, column.mapping_to_display(item))
                self.treeview.item(iid, tags=self.tag_seeker(item))

    def remove(self, idx: int):
        self.treeview.delete(self.rows[idx].iid)
        del self.rows[idx]

    def removes(self, indexes: Iterable[int] = None, *, filter_func: Callable[[Any], bool] = None):
        if indexes is None:
            indexes = range(len(self.rows))

        indexes_to_remove = []
        for idx in indexes:
            row = self.rows[idx]
            if filter_func is None or filter_func(row.item):
                self.treeview.delete(row.iid)
                indexes_to_remove.append(idx)

        self.rows = [row for i, row in enumerate(self.rows) if i not in indexes_to_remove]

    def remove_selected(self, *, filter_func: Callable[[Any], bool] = None):
        self.removes(self.get_selected_indexes(), filter_func=filter_func)

    def reset(self, items: Sequence[Any] = None):
        if items is None:
            items = []

        for row in self.rows:
            self.treeview.delete(row.iid)
        self.rows.clear()

        for item in items:
            self.append(item)

    def grid(self, *, row, column, **kwargs):
        self.treeview.grid(row=row, column=column, **kwargs)

    def config(self, *args, **kwargs):
        self.treeview.config(*args, **kwargs)

    def heading(self, *args, **kwargs):
        self.treeview.heading(*args, **kwargs)

    def tag_configure(self, *args, **kwargs):
        self.treeview.tag_configure(*args, **kwargs)

    def selection_set(self, *indexes: int):
        self.treeview.selection_set([self.rows[idx].iid for idx in indexes])

    def selection_add(self, *indexes: int):
        self.treeview.selection_add([self.rows[idx].iid for idx in indexes])

    def selection_remove(self, *indexes: int):
        self.treeview.selection_remove([self.rows[idx].iid for idx in indexes])

    def selection_clear(self):
        self.treeview.selection_clear()
