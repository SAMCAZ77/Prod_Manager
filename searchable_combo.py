"""
searchable_combo.py
A small reusable Tkinter widget: a text entry with a live-filtered
drop-down list underneath. Used everywhere the app previously required
scrolling a long product list to find a model.
"""

import tkinter as tk
from tkinter import ttk


class SearchableModelPicker(ttk.Frame):
    """
    Type-to-search picker for products.

    - `items` is a list of (model, name) tuples supplied by the caller.
    - As the user types, the drop-down list filters to matching models
      (or product names) in real time -- no more scrolling.
    - `on_select(model, name)` is called when the user picks a row.
    """

    def __init__(self, master, items=None, on_select=None, width=28, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select = on_select
        self.all_items = items or []

        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.insert(0, "")
        self.entry.configure(foreground="#888888")
        self._placeholder_active = True
        self._placeholder_text = "Search model..."
        self.entry.insert(0, self._placeholder_text)

        self.listbox = tk.Listbox(self, height=6, exportselection=False)
        self.listbox.grid(row=1, column=0, sticky="ew")
        self.listbox.grid_remove()  # hidden until the user types

        self.columnconfigure(0, weight=1)

        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Down>", self._focus_listbox)
        self.entry.bind("<Return>", self._select_first)
        self.listbox.bind("<<ListboxSelect>>", self._on_pick)
        self.listbox.bind("<Return>", self._on_pick)
        self.entry.bind("<FocusOut>", self._maybe_hide)
        self.listbox.bind("<FocusOut>", self._maybe_hide)

        self._filtered = []

    # -- public API ------------------------------------------------- #
    def set_items(self, items):
        """Refresh the underlying product list (call after add/edit/delete)."""
        self.all_items = items

    def get_text(self):
        text = self.var.get()
        return "" if self._placeholder_active else text

    def clear(self):
        self.var.set("")
        self._show_placeholder()
        self.listbox.grid_remove()

    # -- internals ---------------------------------------------------- #
    def _clear_placeholder(self, event=None):
        if self._placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.configure(foreground="#000000")
            self._placeholder_active = False

    def _show_placeholder(self):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._placeholder_text)
        self.entry.configure(foreground="#888888")
        self._placeholder_active = True

    def _on_key_release(self, event):
        if event.keysym in ("Down", "Up", "Return"):
            return
        query = self.var.get().strip().lower()
        self.listbox.delete(0, tk.END)
        if not query:
            self.listbox.grid_remove()
            self._filtered = []
            return
        self._filtered = [
            (model, name) for model, name in self.all_items
            if query in model.lower() or query in name.lower()
        ]
        if self._filtered:
            for model, name in self._filtered[:50]:
                self.listbox.insert(tk.END, f"{model}  -  {name}")
            self.listbox.grid()
        else:
            self.listbox.grid_remove()

    def _focus_listbox(self, event):
        if self._filtered:
            self.listbox.grid()
            self.listbox.focus_set()
            self.listbox.selection_set(0)

    def _select_first(self, event):
        if self._filtered:
            self._apply_selection(self._filtered[0])

    def _on_pick(self, event):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self._filtered):
            self._apply_selection(self._filtered[sel[0]])

    def _apply_selection(self, item):
        model, name = item
        self._placeholder_active = False
        self.entry.configure(foreground="#000000")
        self.var.set(model)
        self.listbox.grid_remove()
        if self.on_select:
            self.on_select(model, name)

    def _maybe_hide(self, event=None):
        # small delay so a click on the listbox registers before it hides
        self.after(150, self._hide_if_unfocused)

    def _hide_if_unfocused(self):
        focused = self.focus_get()
        if focused not in (self.entry, self.listbox):
            self.listbox.grid_remove()
