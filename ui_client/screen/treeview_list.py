import tkinter as tk
from tkinter import ttk
from typing import TypeVar, Any, Sequence, Callable, Literal, Iterable
from dataclasses import dataclass


T = TypeVar('T')


@dataclass
class TreeviewRow:
    iid: str
    item: Any

@dataclass
class TreeviewColumn:
    name: str
    mapping_to_display: Callable[[Any], str]


class TreeviewList:
    def __init__(self, parent: tk.Misc, columns: Sequence[TreeviewColumn], **kwargs):
        self.parent = parent
        self.columns = columns
        self.rows: list[TreeviewRow] = []
        self.treeview = ttk.Treeview(parent, columns=[c.name for c in columns], show="headings", **kwargs)

    def _get_display_strings(self, value: Any) -> tuple[str, ...]:
        return tuple(column.mapping_to_display(value) for column in self.columns)

    def insert(self, idx: int | Literal["end"], item: Any):
        if idx == tk.END:
            idx = len(self.rows)

        display_strings = self._get_display_strings(item)

        iid = self.treeview.insert('', idx, values=display_strings)

        self.rows.insert(idx, TreeviewRow(iid, item))

    def append(self, item: Any):
        self.insert(tk.END, item)

    def get(self, idx: int) -> Any:
        return self.rows[idx].item

    def get_items(self) -> list[Any]:
        return [row.item for row in self.rows]

    def get_selected_items(self) -> list[Any]:
        return [row.item for row in self.rows if row.iid in set(self.treeview.selection())]

    def get_selected_indexes(self) -> list[int]:
        return [idx for idx, row in enumerate(self.rows) if row.iid in set(self.treeview.selection())]

    def remove(self, idx: int):
        self.treeview.delete(self.rows[idx].iid)
        del self.rows[idx]

    def removes(self, indexes: Iterable[int] = None, *, filter_func: Callable[[Any], bool]):
        if indexes is None:
            indexes = range(len(self.rows))

        indexes_to_remove = []
        for idx in indexes:
            row = self.rows[idx]
            if filter_func(row.item):
                self.treeview.delete(row.iid)
                indexes_to_remove.append(idx)

        self.rows = [row for i, row in enumerate(self.rows) if i not in indexes_to_remove]

    def reset(self, items: Sequence[Any] = None):
        if items is None:
            items = []

        for row in self.rows:
            self.treeview.delete(row.iid)
        self.rows.clear()

        for item in items:
            self.append(item)

    def grid(self, *, row, column):
        self.treeview.grid(row=row, column=column)

    def config(self, *args, **kwargs):
        self.treeview.config(*args, **kwargs)

    def heading(self, *args, **kwargs):
        self.treeview.heading(*args, **kwargs)
