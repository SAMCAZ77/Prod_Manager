"""
app.py
Main application window for Prod Manager.
Tabs: Products | Production In | Production Out | Movement Log
"""

import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

from database import Database, today_str
from excel_utils import export_to_excel
from searchable_combo import SearchableModelPicker

APP_TITLE = "Prod Manager"
PRIMARY = "#1E3C6E"
ACCENT = "#FFB020"
BG = "#F4F6F9"


class ProdManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x720")
        self.minsize(1000, 620)
        self.configure(bg=BG)

        self._set_icon()
        self._configure_style()

        self.db = Database()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.products_tab = ProductsTab(self.notebook, self.db, self)
        self.prod_in_tab = ProductionTab(self.notebook, self.db, self, mtype="IN")
        self.prod_out_tab = ProductionTab(self.notebook, self.db, self, mtype="OUT")
        self.movement_tab = MovementLogTab(self.notebook, self.db, self)

        self.notebook.add(self.products_tab, text="  Products  ")
        self.notebook.add(self.prod_in_tab, text="  Production In  ")
        self.notebook.add(self.prod_out_tab, text="  Production Out  ")
        self.notebook.add(self.movement_tab, text="  Movement Log  ")

        # All four tabs now exist -- do one final pass so the Production
        # In/Out search-by-model pickers are populated with the current
        # product list at startup.
        self.refresh_all_product_pickers()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_icon(self):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        try:
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except tk.TclError:
            pass

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", PRIMARY)],
                  foreground=[("selected", "#FFFFFF")])
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("TLabel", background=BG, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#FFFFFF", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=BG, font=("Segoe UI", 13, "bold"),
                         foreground=PRIMARY)
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                         background=PRIMARY, foreground="white")
        style.map("Treeview.Heading", background=[("active", PRIMARY)])

    def refresh_all_product_pickers(self):
        """Called whenever the product list changes, so every tab's
        search-by-model picker stays up to date. Safe to call even before
        every tab has been created yet (e.g. during startup)."""
        items = [(row[1], row[2]) for row in self.db.get_products()]
        if hasattr(self, "prod_in_tab"):
            self.prod_in_tab.picker.set_items(items)
        if hasattr(self, "prod_out_tab"):
            self.prod_out_tab.picker.set_items(items)

    def refresh_movement_dependents(self):
        """Safe to call even before every tab has been created yet."""
        if hasattr(self, "movement_tab"):
            self.movement_tab.refresh()
        if hasattr(self, "prod_in_tab"):
            self.prod_in_tab.refresh_table()
        if hasattr(self, "prod_out_tab"):
            self.prod_out_tab.refresh_table()

    def _on_close(self):
        self.db.close()
        self.destroy()


# ---------------------------------------------------------------------- #
# Products tab
# ---------------------------------------------------------------------- #
class ProductsTab(ttk.Frame):
    COLUMNS = ("model", "name", "category", "unit", "unit_price", "stock")
    HEADERS = ["Model", "Product name", "Category", "Unit", "Unit price", "Stock"]

    def __init__(self, master, db: Database, app: ProdManagerApp):
        super().__init__(master)
        self.db = db
        self.app = app
        self.editing_id = None
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        ttk.Label(self, text="Products", style="Header.TLabel").pack(
            anchor="w", padx=14, pady=(12, 4))

        # --- search bar --- #
        top = ttk.Frame(self)
        top.pack(fill="x", padx=14, pady=(0, 8))
        ttk.Label(top, text="Search (model / name):").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_table())
        ttk.Button(top, text="Export to Excel", command=self.export_excel).pack(
            side="right")

        # --- form card --- #
        form = ttk.Frame(self, style="Card.TFrame", padding=12)
        form.pack(fill="x", padx=14, pady=(0, 10))

        self.model_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.unit_var = tk.StringVar(value="pcs")
        self.price_var = tk.StringVar(value="0")
        self.stock_var = tk.StringVar(value="0")

        fields = [
            ("Model *", self.model_var, 16),
            ("Product name *", self.name_var, 20),
            ("Category", self.category_var, 14),
            ("Unit", self.unit_var, 8),
            ("Unit price", self.price_var, 10),
            ("Stock", self.stock_var, 10),
        ]
        for i, (label, var, w) in enumerate(fields):
            ttk.Label(form, text=label, style="Card.TLabel").grid(
                row=0, column=i, sticky="w", padx=6)
            ttk.Entry(form, textvariable=var, width=w).grid(
                row=1, column=i, sticky="w", padx=6, pady=4)

        btn_row = ttk.Frame(form, style="Card.TFrame")
        btn_row.grid(row=2, column=0, columnspan=len(fields), sticky="w", pady=(8, 0))
        ttk.Button(btn_row, text="Add product", style="Accent.TButton",
                   command=self.add_or_update).pack(side="left")
        ttk.Button(btn_row, text="Clear", command=self.clear_form).pack(
            side="left", padx=6)
        ttk.Button(btn_row, text="Delete selected", command=self.delete_selected).pack(
            side="left")

        # --- table --- #
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self.tree.heading(col, text=header)
            self.tree.column(col, anchor="center", width=140)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._load_selected)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._id_map = {}
        for pid, model, name, category, unit, price, stock in self.db.get_products(
                self.search_var.get()):
            iid = self.tree.insert("", "end", values=(
                model, name, category or "", unit or "",
                f"{price:.2f}", f"{stock:g}"))
            self._id_map[iid] = pid
        self.app.refresh_all_product_pickers()

    def _load_selected(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        pid = self._id_map.get(sel[0])
        row = next((r for r in self.db.get_products() if r[0] == pid), None)
        if not row:
            return
        self.editing_id = pid
        _, model, name, category, unit, price, stock = row
        self.model_var.set(model)
        self.name_var.set(name)
        self.category_var.set(category or "")
        self.unit_var.set(unit or "")
        self.price_var.set(str(price))
        self.stock_var.set(str(stock))

    def clear_form(self):
        self.editing_id = None
        self.model_var.set("")
        self.name_var.set("")
        self.category_var.set("")
        self.unit_var.set("pcs")
        self.price_var.set("0")
        self.stock_var.set("0")
        self.tree.selection_remove(self.tree.selection())

    def add_or_update(self):
        model = self.model_var.get().strip()
        name = self.name_var.get().strip()
        if not model or not name:
            messagebox.showwarning(APP_TITLE, "Model and Product name are required.")
            return
        try:
            price = float(self.price_var.get() or 0)
            stock = float(self.stock_var.get() or 0)
        except ValueError:
            messagebox.showwarning(APP_TITLE, "Unit price and Stock must be numbers.")
            return

        if self.editing_id is not None:
            if self.db.model_exists_for_other(model, self.editing_id):
                messagebox.showwarning(APP_TITLE, f"Model '{model}' already exists.")
                return
            self.db.update_product(self.editing_id, model, name,
                                    self.category_var.get(), self.unit_var.get(),
                                    price, stock)
        else:
            existing = self.db.get_product_by_model(model)
            if existing:
                messagebox.showwarning(APP_TITLE, f"Model '{model}' already exists.")
                return
            self.db.add_product(model, name, self.category_var.get(),
                                 self.unit_var.get(), price, stock)

        self.clear_form()
        self.refresh_table()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "Select a product first.")
            return
        if not messagebox.askyesno(APP_TITLE, "Delete the selected product?"):
            return
        pid = self._id_map.get(sel[0])
        if pid:
            self.db.delete_product(pid)
        self.clear_form()
        self.refresh_table()

    def export_excel(self):
        rows = [(m, n, c, u, f"{p:.2f}", f"{s:g}")
                for _, m, n, c, u, p, s in self.db.get_products(self.search_var.get())]
        if not rows:
            messagebox.showinfo(APP_TITLE, "No products to export.")
            return
        default_name = f"Products_{today_str()}.xlsx"
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel workbook", "*.xlsx")],
        )
        if not path:
            return
        export_to_excel(path, "Products", self.HEADERS, rows, sheet_name="Products")
        messagebox.showinfo(APP_TITLE, f"Exported to:\n{path}")


# ---------------------------------------------------------------------- #
# Production In / Production Out tab
# ---------------------------------------------------------------------- #
class ProductionTab(ttk.Frame):
    COLUMNS = ("date", "model", "product_name", "quantity", "operator", "notes")
    HEADERS = ["Date", "Model", "Product name", "Quantity", "Operator", "Notes"]

    def __init__(self, master, db: Database, app: ProdManagerApp, mtype: str):
        super().__init__(master)
        self.db = db
        self.app = app
        self.mtype = mtype  # "IN" or "OUT"
        label = "Production In" if mtype == "IN" else "Production Out"
        self.label = label
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        ttk.Label(self, text=self.label, style="Header.TLabel").pack(
            anchor="w", padx=14, pady=(12, 4))

        # --- add form card --- #
        form = ttk.Frame(self, style="Card.TFrame", padding=12)
        form.pack(fill="x", padx=14, pady=(0, 10))

        ttk.Label(form, text="Model (type to search)", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", padx=6)
        self.picker = SearchableModelPicker(
            form, items=[], on_select=self._on_model_pick, width=26)
        self.picker.grid(row=1, column=0, sticky="w", padx=6, pady=4, rowspan=2)

        ttk.Label(form, text="Product name", style="Card.TLabel").grid(
            row=0, column=1, sticky="w", padx=6)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=22, state="readonly").grid(
            row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Date", style="Card.TLabel").grid(
            row=0, column=2, sticky="w", padx=6)
        self.date_var = tk.StringVar(value=today_str())
        ttk.Entry(form, textvariable=self.date_var, width=12).grid(
            row=1, column=2, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Quantity *", style="Card.TLabel").grid(
            row=0, column=3, sticky="w", padx=6)
        self.qty_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.qty_var, width=10).grid(
            row=1, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Operator", style="Card.TLabel").grid(
            row=0, column=4, sticky="w", padx=6)
        self.operator_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.operator_var, width=14).grid(
            row=1, column=4, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Notes", style="Card.TLabel").grid(
            row=0, column=5, sticky="w", padx=6)
        self.notes_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.notes_var, width=20).grid(
            row=1, column=5, sticky="w", padx=6, pady=4)

        btn_text = "Add Production In" if self.mtype == "IN" else "Add Production Out"
        ttk.Button(form, text=btn_text, style="Accent.TButton",
                   command=self.add_movement).grid(
            row=3, column=0, sticky="w", padx=6, pady=(10, 0))
        ttk.Button(form, text="Clear", command=self.clear_form).grid(
            row=3, column=1, sticky="w", padx=6, pady=(10, 0))

        # --- table + export --- #
        table_top = ttk.Frame(self)
        table_top.pack(fill="x", padx=14)
        ttk.Label(table_top, text=f"{self.label} records", style="TLabel").pack(
            side="left")
        ttk.Button(table_top, text="Export to Excel",
                   command=self.export_excel).pack(side="right")

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(6, 12))

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self.tree.heading(col, text=header)
            self.tree.column(col, anchor="center", width=130)
        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

    def _on_model_pick(self, model, name):
        self.name_var.set(name)

    def clear_form(self):
        self.picker.clear()
        self.name_var.set("")
        self.date_var.set(today_str())
        self.qty_var.set("")
        self.operator_var.set("")
        self.notes_var.set("")

    def add_movement(self):
        model = self.picker.get_text().strip()
        name = self.name_var.get().strip()
        date = self.date_var.get().strip()
        qty_raw = self.qty_var.get().strip()

        if not model or not name:
            messagebox.showwarning(APP_TITLE,
                                    "Pick a product model from the search list.")
            return
        product = self.db.get_product_by_model(model)
        if not product:
            messagebox.showwarning(APP_TITLE,
                                    f"Model '{model}' was not found in Products.")
            return
        if not qty_raw:
            messagebox.showwarning(APP_TITLE, "Quantity is required.")
            return
        try:
            qty = float(qty_raw)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(APP_TITLE, "Quantity must be a positive number.")
            return
        if not date:
            date = today_str()

        self.db.add_movement(self.mtype, date, model, name, qty,
                              self.operator_var.get(), self.notes_var.get())
        self.clear_form()
        self.app.refresh_movement_dependents()
        self.app.refresh_all_product_pickers()

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for mid, mtype, date, model, name, qty, operator, notes in \
                self.db.get_movements(mtype=self.mtype):
            self.tree.insert("", "end", iid=str(mid), values=(
                date, model, name, f"{qty:g}", operator or "", notes or ""))

    def export_excel(self):
        rows = [(date, model, name, f"{qty:g}", operator or "", notes or "")
                for mid, mtype, date, model, name, qty, operator, notes
                in self.db.get_movements(mtype=self.mtype)]
        if not rows:
            messagebox.showinfo(APP_TITLE, "No records to export.")
            return
        default_name = f"{self.label.replace(' ', '_')}_{today_str()}.xlsx"
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel workbook", "*.xlsx")],
        )
        if not path:
            return
        export_to_excel(path, self.label, self.HEADERS, rows, sheet_name=self.label)
        messagebox.showinfo(APP_TITLE, f"Exported to:\n{path}")


# ---------------------------------------------------------------------- #
# Movement log tab
# ---------------------------------------------------------------------- #
class MovementLogTab(ttk.Frame):
    COLUMNS = ("type", "date", "model", "product_name", "quantity", "operator", "notes")
    HEADERS = ["Type", "Date", "Model", "Product name", "Quantity", "Operator", "Notes"]

    def __init__(self, master, db: Database, app: ProdManagerApp):
        super().__init__(master)
        self.db = db
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        ttk.Label(self, text="Movement Log", style="Header.TLabel").pack(
            anchor="w", padx=14, pady=(12, 4))

        filt = ttk.Frame(self)
        filt.pack(fill="x", padx=14, pady=(0, 8))

        ttk.Label(filt, text="Search by model:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filt, textvariable=self.search_var, width=22)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        ttk.Label(filt, text="Type:").pack(side="left", padx=(14, 0))
        self.type_var = tk.StringVar(value="All")
        type_box = ttk.Combobox(filt, textvariable=self.type_var, width=8,
                                 state="readonly", values=["All", "IN", "OUT"])
        type_box.pack(side="left", padx=6)
        type_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(filt, text="From (YYYY-MM-DD):").pack(side="left", padx=(14, 0))
        self.from_var = tk.StringVar()
        ttk.Entry(filt, textvariable=self.from_var, width=12).pack(side="left", padx=6)

        ttk.Label(filt, text="To:").pack(side="left")
        self.to_var = tk.StringVar()
        ttk.Entry(filt, textvariable=self.to_var, width=12).pack(side="left", padx=6)

        ttk.Button(filt, text="Apply filter", command=self.refresh).pack(
            side="left", padx=10)
        ttk.Button(filt, text="Clear filter", command=self.clear_filter).pack(
            side="left")
        ttk.Button(filt, text="Export to Excel", command=self.export_excel).pack(
            side="right")

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self.tree.heading(col, text=header)
            self.tree.column(col, anchor="center", width=120)
        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

    def clear_filter(self):
        self.search_var.set("")
        self.type_var.set("All")
        self.from_var.set("")
        self.to_var.set("")
        self.refresh()

    def _current_rows(self):
        mtype = None if self.type_var.get() == "All" else self.type_var.get()
        return self.db.get_movements(
            mtype=mtype,
            search=self.search_var.get(),
            date_from=self.from_var.get().strip() or None,
            date_to=self.to_var.get().strip() or None,
        )

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for mid, mtype, date, model, name, qty, operator, notes in self._current_rows():
            self.tree.insert("", "end", values=(
                mtype, date, model, name, f"{qty:g}", operator or "", notes or ""))

    def export_excel(self):
        rows = [(mtype, date, model, name, f"{qty:g}", operator or "", notes or "")
                for mid, mtype, date, model, name, qty, operator, notes
                in self._current_rows()]
        if not rows:
            messagebox.showinfo(APP_TITLE, "No records to export.")
            return
        default_name = f"Movement_Log_{today_str()}.xlsx"
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel workbook", "*.xlsx")],
        )
        if not path:
            return
        export_to_excel(path, "Movement Log", self.HEADERS, rows,
                         sheet_name="Movement Log")
        messagebox.showinfo(APP_TITLE, f"Exported to:\n{path}")

